#!/usr/bin/env python3
"""
Generador de detalles de carga para usar con Postman Runner.

Genera una serie de objetos JSON con la estructura:
{
  "masaAcumulada": 119.5,
  "densidad": 0.83,
  "temperatura": 20.3,
  "caudal": 5.8,
  "orden": { "id": 123 }
}

Características principales:
- Configurable: iteraciones, id de orden, masa final, umbral de temperatura, probabilidades de valores "erróneos".
- La masa se acumula hasta `final_mass`, con variación realista en los incrementos.
- Genera ocasionalmente valores inválidos según probabilidades (caudal<=0, masa<=0 o decreciente, densidad fuera de [0,1]).
- Salida en formato JSON (array) o NDJSON (una línea por objeto).

Uso ejemplo:
  python3 generadorDetallesDeOrden.py --iterations 200 --order_id 42 --final_mass 1200 --temp_threshold 45 --output detalles.json

Este archivo puede usarse como Data File en Postman Runner (formato JSON: array of objects).
"""

import argparse
import json
import random
from pathlib import Path
from typing import List

# --------------------
# Valores por defecto (editar manualmente aquí)
# --------------------
# ID de la orden que recibirán todos los detalles
DEFAULT_ORDER_ID = 25
# Cantidad de iteraciones (detalles) a generar
DEFAULT_ITERATIONS = 100
# Masa acumulada objetivo en la última iteración (kg)
DEFAULT_FINAL_MASS = 2500

#-------------------------------------------------------------------------------------------------------------
# MODIFICAR PROBABILIDADES POR DEFECTO AQUÍ SI SE DESEA (0.02 es 2%)
def parse_args():
	p = argparse.ArgumentParser(description='Generador de detalles de carga para Postman Runner')
	p.add_argument('--iterations', '-n', type=int, default=DEFAULT_ITERATIONS, help='Cantidad de detalles a generar')
	p.add_argument('--order_id', type=int, default=DEFAULT_ORDER_ID, help='ID de la orden (entero)')
	p.add_argument('--final_mass', type=float, default=DEFAULT_FINAL_MASS, help='Masa acumulada objetivo en la última iteración (kg)')
	p.add_argument('--start_mass', type=float, default=0.0, help='Masa inicial (kg)')
	p.add_argument('--temp_threshold', type=float, default=30.0, help='Umbral de temperatura para alarma (°C)')
	p.add_argument('--output', '-o', default='detalles.json', help='Archivo de salida (JSON array)')
	p.add_argument('--format', choices=['json','ndjson'], default='json', help='Formato de salida: json (array) o ndjson (one-line per object)')
	p.add_argument('--prob_bad_caudal', type=float, default=0.03, help='Probabilidad por iteración de generar caudal <= 0')
	p.add_argument('--prob_bad_mass', type=float, default=0.02, help='Probabilidad por iteración de generar masa inválida (<=0 o decreciente)')
	p.add_argument('--prob_bad_density', type=float, default=0.02, help='Probabilidad por iteración de densidad fuera de rango [0,1]')
	p.add_argument('--prob_high_temp', type=float, default=0.05, help='Probabilidad por iteración de superar el umbral de temperatura')
	p.add_argument('--seed', type=int, default=None, help='Semilla aleatoria (opcional)')
	return p.parse_args()
#-------------------------------------------------------------------------------------------------------------


def generate_increments(iterations: int, total: float, start: float, rng: random.Random) -> List[float]:
	"""Genera una lista de incrementos que suman (total - start), con variabilidad realista."""
	remaining = max(0.0, total - start)
	if iterations <= 0:
		return []

	base = remaining / iterations if iterations else 0.0
	# generar valores positivos con ruido
	incs = []
	for _ in range(iterations):
		# gaussiano centrado en base con desviación relativa
		val = rng.gauss(base, max(0.001, base * 0.4))
		if val < 0:
			val = rng.uniform(0.0, base * 0.2)
		incs.append(val)

	sum_incs = sum(incs)
	if sum_incs <= 0:
		# repartir equitativamente
		return [remaining / iterations] * iterations

	# escalar para que sumen exactamente remaining
	factor = remaining / sum_incs
	incs = [v * factor for v in incs]
	return incs


def clamp(x, a, b):
	return max(a, min(b, x))


def build_details(args):
	rng = random.Random(args.seed)
	incs = generate_increments(args.iterations, args.final_mass, args.start_mass, rng)

	records = []
	# masa verdadera que acumula los incrementos y garantiza llegar a final_mass
	true_masa = args.start_mass

	for i, inc in enumerate(incs):
		prev_true = true_masa
		true_masa = prev_true + inc

		# densidad: por defecto en rango [0.7,0.9]
		dens = rng.uniform(0.70, 0.90)
		if rng.random() < args.prob_bad_density:
			# densidad fuera de rango; can be <0 o >1
			if rng.random() < 0.5:
				dens = -abs(rng.uniform(0.01, 0.5))
			else:
				dens = 1.0 + rng.uniform(0.01, 0.8)

		# caudal: tomar inc y convertir a kg/h de forma aproximada
		# suponemos cada iteración equivale a 1 segundo, entonces caudal ~ inc * 3600
		caudal = inc * 3600.0
		# añadir variabilidad
		caudal *= rng.uniform(0.6, 1.4)
		if rng.random() < args.prob_bad_caudal:
			# problema en caudal
			caudal = rng.choice([0.0, -abs(rng.uniform(0.0, 200.0))])

		# temperatura: base normal 18-28 C
		temp = rng.gauss(20.0, 1.8)
		# ocasionalmente superar umbral (simular alarma realista)
		# vamos a dar una probabilidad pequeña de superar umbral
		if rng.random() < args.prob_high_temp:
			temp = args.temp_threshold + rng.uniform(0.1, 8.0)

		# masa inválida / decreciente ocasional (afecta sólo al valor reportado)
		if rng.random() < args.prob_bad_mass:
			if rng.random() < 0.5:
				# reporte una masa menor que la anterior (decremento)
				reported_masa = prev_true - rng.uniform(1.0, max(1.0, prev_true * 0.2))
			else:
				# reporte una masa negativa o cero
				reported_masa = rng.uniform(-50.0, 0.0)
		else:
			# reporte normal: la masa verdadera acumulada
			reported_masa = true_masa

		# garantizar que la última iteración reporte exactamente final_mass
		if i == len(incs) - 1:
			reported_masa = args.final_mass

		# asegurar redondeo y tipos (solo campo plano 'orden_id')
		record = {
			"masaAcumulada": round(reported_masa, 3),
			"densidad": round(dens, 6),
			"temperatura": round(temp, 3),
			"caudal": round(caudal, 3),
			"orden_id": args.order_id
		}

		records.append(record)

		# continuar

	return records


def main():
	args = parse_args()
	records = build_details(args)

	out_path = Path(args.output).expanduser()
	if args.format == 'json':
		with open(out_path, 'w', encoding='utf-8') as f:
			json.dump(records, f, ensure_ascii=False, indent=2)
	else:
		# ndjson
		with open(out_path, 'w', encoding='utf-8') as f:
			for r in records:
				f.write(json.dumps(r, ensure_ascii=False) + '\n')

	print(f"Generados {len(records)} registros en: {out_path}")


if __name__ == '__main__':
	main()

