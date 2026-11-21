"""Pruebas integrales con PostgreSQL REAL, nunca SQLite.

Solo se ejecutan con ECO_TEST_DATABASE_URL y DATABASE_URL iguales y apuntando
EXACTAMENTE a una base denominada 'ecoconecta_test'.

Estas pruebas crean/borran tablas en la base DE PRUEBAS. Nunca use la base demo o productiva.
"""
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.engine.url import make_url

DATABASE_URL = os.environ.get('DATABASE_URL', '')
TEST_URL = os.environ.get('ECO_TEST_DATABASE_URL', '')
if not TEST_URL or DATABASE_URL != TEST_URL or make_url(TEST_URL).database != 'ecoconecta_test':
    pytest.skip('Prueba PostgreSQL deshabilitada fuera de ecoconecta_test', allow_module_level=True)

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import app
from app.db import Base, engine
from app import models
from app.security import hash_password


def test_flujos_y_permisos_completos():
    # Aislamiento deliberado: únicamente la BD ecoconecta_test.
    with engine.begin() as connection:
        Base.metadata.drop_all(connection)
        Base.metadata.create_all(connection)
    credentials = {
        'admin': ('admin@demo.invalid', 'TestAdminPassword2026', ['administrador']),
        'huerta': ('huerta@demo.invalid', 'TestHuertaPassword2026', ['coordinador_huerta', 'huertero']),
        'reciclaje': ('reciclaje@demo.invalid', 'TestReciclajePassword2026', ['coordinador_reciclaje', 'reciclador']),
    }
    with Session(engine) as db:
        for name, (email, password, roles) in credentials.items():
            user = models.Usuario(nombre=name, correo=email, contrasena_hash=hash_password(password))
            db.add(user)
            db.flush()
            for role in roles:
                db.add(models.UsuarioRol(usuario_id=user.id, rol=role))
        db.commit()
    with TestClient(app) as client:
        headers = {}
        def request(role, method, path, json=None, expect=200):
            response = client.request(method, path, json=json, headers=headers[role])
            assert response.status_code == expect, (role,method,path,response.status_code,response.text)
            return response.json() if response.content else None
        for role,(email,password,_) in credentials.items():
            response=client.post('/api/auth/login',json={'correo':email,'contrasena':password})
            assert response.status_code==200,response.text
            headers[role]={'Authorization': 'Bearer '+response.json()['token']}
            assert request(role,'GET','/api/auth/me')['roles']

        request('admin','PUT','/api/admin/regla-puntos',{
            'puntos_por_kg':2,'nombre':'Regla demo CI no oficial'})
        totals=[]
        for flow,owner,wrong,peso in [
            ('organicos','huerta','reciclaje','3.00'),
            ('reciclables','reciclaje','huerta','2.00'),
        ]:
            ci=request('admin','POST','/api/ciudadanos',{
                'telefono':f'DEMO-TEST-{flow}', 'nombre':'Ciudadano ficticio',
                'direccion':'Villas de San Pablo, manzana ficticia 1',
                'tipo_generador':'unidad_productiva' if flow=='organicos' else 'hogar',
                'consentimiento':True,'habilitado_piloto':True,
            })['id']
            solicitud=request('admin','POST','/api/solicitudes',{
                'ciudadano_id':ci,'flujo':flow,'observaciones':'TEST FICTICIO',
                'preferencia_horaria':'Mañana en la tarde',
            })
            sid=solicitud['id']
            assert solicitud['estado']=='recibida'
            request(wrong,'GET',f'/api/solicitudes/{sid}',expect=404)
            request(owner,'POST',f'/api/solicitudes/{sid}/programar',
                    {'fecha_hora':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()},expect=409)
            request(owner,'POST',f'/api/solicitudes/{sid}/revisar')
            people=request(owner,'GET','/api/personal')
            collector=next(p for p in people if owner in ('huerta','reciclaje') and
                           ('huertero' if owner=='huerta' else 'reciclador') in p['roles'])
            wrong_people=request(wrong,'GET','/api/personal')
            wrong_collector=next(p for p in wrong_people if
                                 ('reciclador' if owner=='huerta' else 'huertero') in p['roles'])
            request(owner,'POST',f'/api/solicitudes/{sid}/asignar',
                    {'recolector_id':wrong_collector['id']},expect=422)
            request(owner,'POST',f'/api/solicitudes/{sid}/asignar',
                    {'recolector_id':collector['id']})
            request(owner,'POST',f'/api/solicitudes/{sid}/programar',
                    {'fecha_hora':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()})
            before=request('admin','GET','/api/admin/resumen')['puntos']
            assert before==sum(totals)
            completed=request(owner,'POST',f'/api/solicitudes/{sid}/recolectar',
                              {'cantidad_recibida':peso,'unidad':'kg'})
            points=int(Decimal(peso)*2)
            assert completed['estado']=='recolectada' and completed['puntos']==points
            totals.append(points)
            after=request('admin','GET','/api/admin/resumen')['puntos']
            assert after-before==points
            request(owner,'POST',f'/api/solicitudes/{sid}/recolectar',
                    {'cantidad_recibida':peso,'unidad':'kg'},expect=409)
            detail=request(owner,'GET',f'/api/solicitudes/{sid}')
            assert detail['estado']=='recolectada' and len(detail['historial'])>=4
        report=client.get('/api/admin/exportar-csv',headers=headers['admin'])
        assert report.status_code==200 and 'recolectada' in report.text
        report_other=client.get('/api/admin/exportar-csv',headers=headers['huerta'])
        assert report_other.status_code==403
        assert request('admin','GET','/api/admin/resumen')['puntos']==10
        request('admin','POST','/api/auth/logout')
        response=client.get('/api/auth/me',headers=headers['admin'])
        assert response.status_code==401, 'El token debe quedar revocado al cerrar sesion'
