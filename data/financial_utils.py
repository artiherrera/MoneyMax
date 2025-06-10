import pandas as pd
import json
import os

def obtener_producto_por_id(producto_id):
    """Obtiene un producto específico por su ID (compatibilidad)"""
    # Esta función se mantiene por compatibilidad
    # En Flask usamos directamente el JSON
    return None

def obtener_tasa_producto(producto, plazo_dias):
    """Obtiene la tasa de un producto según el plazo (compatibilidad)"""
    # En Flask manejamos las tasas directamente del JSON
    return 0.0

def calcular_inversion_simple(monto_inicial, tasa_anual, plazo_dias):
    """
    Calcula inversión de monto único (una sola vez)
    
    Args:
        monto_inicial (float): Monto a invertir
        tasa_anual (float): Tasa anual en porcentaje
        plazo_dias (int): Plazo en días
    
    Returns:
        dict: Resultados del cálculo
    """
    # Convertir tasa anual a decimal
    tasa_decimal = tasa_anual / 100
    
    # Calcular rendimiento
    rendimiento_total = monto_inicial * tasa_decimal * (plazo_dias / 365)
    monto_final = monto_inicial + rendimiento_total
    
    # Calcular tasa efectiva anual
    if plazo_dias > 0:
        tasa_efectiva = ((monto_final / monto_inicial) ** (365 / plazo_dias) - 1) * 100
    else:
        tasa_efectiva = tasa_anual
    
    return {
        'monto_inicial': round(monto_inicial, 2),
        'monto_final': round(monto_final, 2),
        'rendimiento_total': round(rendimiento_total, 2),
        'tasa_anual': tasa_anual,
        'tasa_efectiva': round(tasa_efectiva, 2),
        'plazo_dias': plazo_dias,
        'plazo_meses': round(plazo_dias / 30.44, 1),
        'tipo_inversion': 'simple'
    }

def calcular_inversion_mensual(monto_mensual, tasa_anual, num_meses):
    """
    Calcula inversión con aportaciones mensuales constantes
    
    Args:
        monto_mensual (float): Monto mensual a invertir
        tasa_anual (float): Tasa anual en porcentaje
        num_meses (int): Número de meses
    
    Returns:
        dict: Resultados del cálculo
    """
    tasa_mensual = (tasa_anual / 100) / 12
    
    # Fórmula de anualidad ordinaria
    if tasa_mensual == 0:
        monto_final = monto_mensual * num_meses
    else:
        monto_final = monto_mensual * (((1 + tasa_mensual) ** num_meses - 1) / tasa_mensual)
    
    total_aportado = monto_mensual * num_meses
    rendimiento_total = monto_final - total_aportado
    
    return {
        'monto_mensual': round(monto_mensual, 2),
        'total_aportado': round(total_aportado, 2),
        'monto_final': round(monto_final, 2),
        'rendimiento_total': round(rendimiento_total, 2),
        'tasa_anual': tasa_anual,
        'num_meses': num_meses,
        'rendimiento_porcentual': round((rendimiento_total / total_aportado) * 100, 2) if total_aportado > 0 else 0,
        'tipo_inversion': 'mensual'
    }

def generar_tabla_crecimiento_simple(monto_inicial, tasa_anual, plazo_dias):
    """
    Para inversión simple NO genera tabla de crecimiento
    Solo retorna un DataFrame vacío ya que no hay evolución mes a mes
    """
    # Para inversión única no tiene sentido mostrar evolución
    # ya que es un solo monto que se invierte una vez
    return pd.DataFrame()

def generar_tabla_crecimiento_mensual(monto_mensual, tasa_anual, num_meses):
    """Genera tabla de crecimiento mes a mes para inversión mensual"""
    
    datos = []
    tasa_mensual = (tasa_anual / 100) / 12
    monto_acumulado = 0
    total_aportaciones = 0
    
    for mes in range(1, num_meses + 1):
        # Agregar nueva aportación al inicio del mes
        total_aportaciones += monto_mensual
        monto_acumulado += monto_mensual
        
        # Calcular rendimientos sobre el saldo total acumulado al final del mes
        rendimiento_mes = monto_acumulado * tasa_mensual
        monto_acumulado += rendimiento_mes
        
        # Calcular totales
        total_rendimientos = monto_acumulado - total_aportaciones
        
        datos.append({
            'mes': mes,
            'aportacion': monto_mensual,
            'total_aportado': round(total_aportaciones, 2),
            'rendimiento_mes': round(rendimiento_mes, 2),
            'total_rendimientos': round(total_rendimientos, 2),
            'monto_total': round(monto_acumulado, 2)
        })
    
    return pd.DataFrame(datos)

def validar_parametros_inversion(monto, plazo_dias, producto_id, tipo_inversion='simple'):
    """
    Valida que los parámetros de inversión sean correctos
    
    Args:
        monto: Monto a invertir (o monto mensual)
        plazo_dias: Plazo en días del producto
        producto_id: ID del producto
        tipo_inversion: 'simple' o 'mensual'
    
    Returns:
        dict: {'valido': bool, 'errores': list}
    """
    errores = []
    
    # Validar monto
    try:
        monto = float(monto)
    except (ValueError, TypeError):
        errores.append("El monto debe ser un número válido")
        return {'valido': False, 'errores': errores}
    
    # Límites según tipo de inversión
    if tipo_inversion == 'simple':
        MONTO_MIN = 100
        MONTO_MAX = 50_000_000
        tipo_monto = "El monto a invertir"
    else:
        MONTO_MIN = 100
        MONTO_MAX = 1_000_000  # Límite más bajo para mensualidades
        tipo_monto = "El monto mensual"
    
    if monto <= 0:
        errores.append(f"{tipo_monto} debe ser mayor a cero")
    elif monto < MONTO_MIN:
        errores.append(f"{tipo_monto} mínimo es ${MONTO_MIN:,} MXN")
    elif monto > MONTO_MAX:
        errores.append(f"{tipo_monto} máximo es ${MONTO_MAX:,} MXN")
    
    # Validar plazo
    if plazo_dias < 0:
        errores.append("El plazo debe ser mayor o igual a cero días")
    elif plazo_dias > 3650:  # 10 años
        errores.append("El plazo máximo es 10 años")
    
    # Validar producto
    if not producto_id:
        errores.append("Debe especificar un producto")
    
    return {
        'valido': len(errores) == 0,
        'errores': errores
    }

def formatear_moneda(cantidad):
    """Formatea una cantidad como moneda mexicana"""
    if cantidad is None:
        return "$0.00 MXN"
    
    try:
        return f"${cantidad:,.2f} MXN"
    except (ValueError, TypeError):
        return "$0.00 MXN"

def calcular_tasa_efectiva_anual(monto_inicial, monto_final, plazo_dias):
    """Calcula la tasa efectiva anual"""
    if monto_inicial <= 0 or plazo_dias <= 0:
        return 0
    
    try:
        tasa_efectiva = ((monto_final / monto_inicial) ** (365 / plazo_dias) - 1) * 100
        return round(tasa_efectiva, 2)
    except (ZeroDivisionError, ValueError):
        return 0

def convertir_dias_a_meses(dias):
    """Convierte días a meses (promedio de 30.44 días por mes)"""
    return round(dias / 30.44, 1)

def convertir_meses_a_dias(meses):
    """Convierte meses a días (promedio de 30.44 días por mes)"""
    return round(meses * 30.44)

def calcular_comparacion_productos(monto, plazo_dias, productos_dict):
    """
    Compara el rendimiento entre diferentes productos para un mismo monto y plazo
    
    Args:
        monto: Monto a invertir
        plazo_dias: Plazo deseado
        productos_dict: Diccionario con los productos
    
    Returns:
        list: Lista de resultados ordenados por rendimiento
    """
    resultados = []
    
    for producto_id, producto in productos_dict.items():
        # Buscar el plazo más cercano
        plazos_disponibles = [int(p) for p in producto['plazos'].keys()]
        plazo_cercano = min(plazos_disponibles, key=lambda x: abs(x - plazo_dias))
        
        if str(plazo_cercano) in producto['plazos']:
            plazo_info = producto['plazos'][str(plazo_cercano)]
            
            # Solo calcular si permite inversión única
            if plazo_info.get('permite_inversion_unica', True):
                calc = calcular_inversion_simple(
                    monto, 
                    plazo_info['tasa_anual'], 
                    plazo_cercano
                )
                
                resultados.append({
                    'producto': producto['nombre'],
                    'producto_id': producto_id,
                    'plazo_dias': plazo_cercano,
                    'tasa_anual': plazo_info['tasa_anual'],
                    'rendimiento': calc['rendimiento_total'],
                    'monto_final': calc['monto_final']
                })
    
    # Ordenar por rendimiento descendente
    return sorted(resultados, key=lambda x: x['rendimiento'], reverse=True)