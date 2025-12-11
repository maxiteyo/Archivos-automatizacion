#!/usr/bin/env python3
"""
Generador de archivos JSON para órdenes SAP.

Genera automáticamente valores únicos para: order_code, codigo_cliente, patente,
codigo_camion, codigo_chofer y codigo_producto en cada ejecución.

Permite sobrescribir cualquier campo mediante argumentos de línea de comandos.

Uso rápido:
  python3 generadorOrdenesSap.py
  python3 generadorOrdenesSap.py --order_code "SAP-2026-999" --patente ABC12345 --output pedido.json

El archivo JSON se guarda en la misma carpeta del script (por defecto con nombre: <order_code>.json).
"""

import argparse
import json
import random
import string
from datetime import datetime
from pathlib import Path


def generate_order_code():
	year = datetime.now().year
	suffix = random.randint(100, 999999)
	return f"SAP-{year}-{suffix}"


def generate_codigo(prefix, digits=5):
	number = random.randint(1, 10**digits - 1)
	return f"{prefix}-{number:0{digits}d}"


def generate_patente():
	# Patrón simple: 2 letras + 5 dígitos (ej: GF56726)
	letras = ''.join(random.choices(string.ascii_uppercase, k=2))
	numeros = ''.join(random.choices(string.digits, k=5))
	return f"{letras}{numeros}"


def build_default_payload():
	return {
		"order_code": generate_order_code(),
		"preset": 2500.0,
		"fechaPrevistaCarga": "2025-11-16T14:00:00-0300",
		"cliente": {
			"razonSocial": "Shell",
			"codigo_cliente": generate_codigo('CLI', 5),
			"contacto": "+54 11 5555-1112"
		},
		"camion": {
			"patente": generate_patente(),
			"codigo_camion": generate_codigo('TRK', 5),
			"descripcion": "Camión cisterna aluminio",
			"cisternado": [10000, 2500]
		},
		"chofer": {
			"documento": "30151231",
			"codigo_chofer": generate_codigo('DRV', 6),
			"nombre": "Juan",
			"apellido": "Pérez"
		},
		"producto": {
			"nombre": "Butano",
			"codigo_producto": generate_codigo('PROD', 6),
			"descripcion": "Combustible para calefaccion"
		}
	}


def parse_args():
	p = argparse.ArgumentParser(description='Generador de archivos JSON para órdenes SAP')

	# Principales
	p.add_argument('--order_code', help='Código de orden (ej: SAP-2025-136)')
	p.add_argument('--preset', type=float, help='Preset (float)')
	p.add_argument('--fechaPrevistaCarga', help='Fecha prevista (string)')
	p.add_argument('--output', help='Nombre de archivo de salida (por defecto: <order_code>.json)')
	p.add_argument('--overwrite', action='store_true', help='Si se setea, escribe siempre en un único archivo (por defecto "ordenSap.json") en vez de crear uno nuevo por order_code')

	# Cliente
	p.add_argument('--cliente_razonSocial', help='Razón social cliente')
	p.add_argument('--codigo_cliente', help='Código cliente (ej: CLI-00036)')
	p.add_argument('--cliente_contacto', help='Contacto cliente')

	# Camión
	p.add_argument('--patente', help='Patente del camión (ej: GF56726)')
	p.add_argument('--codigo_camion', help='Código camión (ej: TRK-00036)')
	p.add_argument('--descripcion_camion', help='Descripción del camión')
	p.add_argument('--cisternado', help='Cisternado como lista separada por comas, ej: 10000,2500')

	# Chofer
	p.add_argument('--documento', help='Documento del chofer')
	p.add_argument('--codigo_chofer', help='Código chofer (ej: DRV-30111196)')
	p.add_argument('--chofer_nombre', help='Nombre del chofer')
	p.add_argument('--chofer_apellido', help='Apellido del chofer')

	# Producto
	p.add_argument('--producto_nombre', help='Nombre del producto')
	p.add_argument('--codigo_producto', help='Código del producto (ej: PROD-77626)')
	p.add_argument('--producto_descripcion', help='Descripción del producto')

	return p.parse_args()


def apply_overrides(payload, args):
	if args.order_code:
		payload['order_code'] = args.order_code
	if args.preset is not None:
		payload['preset'] = args.preset
	if args.fechaPrevistaCarga:
		payload['fechaPrevistaCarga'] = args.fechaPrevistaCarga

	# Cliente
	if args.cliente_razonSocial:
		payload['cliente']['razonSocial'] = args.cliente_razonSocial
	if args.codigo_cliente:
		payload['cliente']['codigo_cliente'] = args.codigo_cliente
	if args.cliente_contacto:
		payload['cliente']['contacto'] = args.cliente_contacto

	# Camión
	if args.patente:
		payload['camion']['patente'] = args.patente
	if args.codigo_camion:
		payload['camion']['codigo_camion'] = args.codigo_camion
	if args.descripcion_camion:
		payload['camion']['descripcion'] = args.descripcion_camion
	if args.cisternado:
		parts = [p.strip() for p in args.cisternado.split(',') if p.strip()]
		try:
			nums = [int(x) for x in parts]
			payload['camion']['cisternado'] = nums
		except ValueError:
			pass

	# Chofer
	if args.documento:
		payload['chofer']['documento'] = args.documento
	if args.codigo_chofer:
		payload['chofer']['codigo_chofer'] = args.codigo_chofer
	if args.chofer_nombre:
		payload['chofer']['nombre'] = args.chofer_nombre
	if args.chofer_apellido:
		payload['chofer']['apellido'] = args.chofer_apellido

	# Producto
	if args.producto_nombre:
		payload['producto']['nombre'] = args.producto_nombre
	if args.codigo_producto:
		payload['producto']['codigo_producto'] = args.codigo_producto
	if args.producto_descripcion:
		payload['producto']['descripcion'] = args.producto_descripcion

	return payload


def main():
	args = parse_args()
	payload = build_default_payload()

	# Aplicar overrides de args (si se pasan)
	payload = apply_overrides(payload, args)

	# Nombre de archivo
	# siempre sobrescribe por defecto usando 'ordenSap.JSON' si no diste --output
	output_name = args.output if args.output else 'ordenSap.JSON'

	out_path = Path(__file__).resolve().parent / output_name

	with open(out_path, 'w', encoding='utf-8') as f:
		json.dump(payload, f, ensure_ascii=False, indent=4)

	print(f"Archivo JSON generado: {out_path}")


if __name__ == '__main__':
	main()

{
"order_code": "SAP-2025-136",
"preset": 2500.0,
"fechaPrevistaCarga": "2025-11-16T14:00:00-0300",
"cliente": {
"razonSocial": "Shell",
"codigo_cliente": "CLI-00036",
"contacto": "+54 11 5555-1112"
},
"camion": {
"patente": "GF56726",
"codigo_camion": "TRK-00036",
"descripcion": "Camión cisterna aluminio",
"cisternado": [10000,2500]
},
"chofer": {
"documento": "30151231",
"codigo_chofer": "DRV-30111196",
"nombre": "Juan",
"apellido": "Pérez"
},
"producto": {
"nombre": "Butano",
"codigo_producto": "PROD-77626",
"descripcion": "Combustible para calefaccion"
}
}