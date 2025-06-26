import pandas as pd
import json
import os

def obtener_producto_por_id(producto_id):
    """Obtiene un producto específico por su ID (compatibilidad)"""
    # Esta función se mantiene por compatibilidad
    # En Flask usamos directamente el JSON
    return None

def obtener_tasa_producto(producto, plazo_dias):
    """Obtiene la tasa anual de un producto para un plazo específico"""
    try:
        plazo_str = str(plazo_dias)
        if plazo_str in producto['plazos']:
            return producto['plazos'][plazo_str]['tasa_anual']
        else:
            raise ValueError(f"Plazo {plazo_dias} días no disponible para este producto")
    except KeyError as e:
        raise ValueError(f"Error al obtener tasa: {e}")

def validar_parametros_inversion(monto, plazo_dias, producto_id, tipo_inversion):
    """Valida los parámetros de inversión"""
    errores = []
    
    # Validación de monto
    try:
        monto = float(monto)
    except (ValueError, TypeError):
        errores.append("El monto debe ser un número válido")
        return {'valido': False, 'errores': errores}
    
    # Límites según tipo de inversión
    if tipo_inversion == 'simple':
        MONTO_MIN = 100
        MONTO_MAX = 50_000_000
    else:  # mensual
        MONTO_MIN = 100
        MONTO_MAX = 1_000_000
    
    if not (MONTO_MIN <= monto <= MONTO_MAX):
        errores.append(f"El monto debe estar entre ${MONTO_MIN:,} y ${MONTO_MAX:,} MXN")
    
    # Validación de plazo
    try:
        plazo_dias = int(plazo_dias)
    except (ValueError, TypeError):
        errores.append("El plazo debe ser un número válido")
        return {'valido': False, 'errores': errores}
    
    if not (1 <= plazo_dias <= 3650):
        errores.append("El plazo debe estar entre 1 y 3650 días")
    
    return {'valido': len(errores) == 0, 'errores': errores}

def calcular_inversion_simple(monto_inicial, tasa_anual, plazo_dias):
    """
    Calcula rendimiento para inversión única
    
    Args:
        monto_inicial (float): Monto a invertir
        tasa_anual (float): Tasa anual en porcentaje
        plazo_dias (int): Días de inversión
    
    Returns:
        dict: Resultados del cálculo
    """
    try:
        # Conversiones
        monto_inicial = float(monto_inicial)
        tasa_anual = float(tasa_anual)
        plazo_dias = int(plazo_dias)
        
        # Cálculos
        tasa_diaria = tasa_anual / 36500  # Dividir entre 365 días y convertir de % a decimal
        rendimiento = monto_inicial * tasa_diaria * plazo_dias
        monto_final = monto_inicial + rendimiento
        
        # Tasa efectiva anual
        if plazo_dias > 0:
            factor_crecimiento = monto_final / monto_inicial
            periodos_anuales = 365 / plazo_dias
            tasa_efectiva = (factor_crecimiento ** periodos_anuales - 1) * 100
        else:
            tasa_efectiva = 0
        
        # Convertir días a meses para mostrar
        plazo_meses = round(plazo_dias / 30.44, 1)  # 30.44 es el promedio de días por mes
        
        return {
            'tipo_inversion': 'simple',
            'monto_inicial': round(monto_inicial, 2),
            'rendimiento': round(rendimiento, 2),
            'monto_final': round(monto_final, 2),
            'tasa_efectiva': round(tasa_efectiva, 2),
            'plazo_meses': plazo_meses,
            'tasa_anual': tasa_anual,
            'plazo_dias': plazo_dias
        }
        
    except Exception as e:
        raise ValueError(f"Error en cálculo de inversión simple: {str(e)}")

def calcular_inversion_mensual(monto_mensual, tasa_anual, plazo_meses):
    """
    Calcula rendimiento para inversión mensual (anualidad ordinaria)
    
    Args:
        monto_mensual (float): Monto mensual a invertir
        tasa_anual (float): Tasa anual en porcentaje
        plazo_meses (int): Número de meses
    
    Returns:
        dict: Resultados del cálculo
    """
    try:
        # Conversiones
        monto_mensual = float(monto_mensual)
        tasa_anual = float(tasa_anual)
        plazo_meses = int(plazo_meses)
        
        # Tasa mensual
        tasa_mensual = (tasa_anual / 100) / 12
        
        # Fórmula de anualidad ordinaria: FV = PMT * [((1 + r)^n - 1) / r]
        if tasa_mensual > 0:
            factor = ((1 + tasa_mensual) ** plazo_meses - 1) / tasa_mensual
            monto_final = monto_mensual * factor
        else:
            monto_final = monto_mensual * plazo_meses
        
        total_aportado = monto_mensual * plazo_meses
        rendimiento_total = monto_final - total_aportado
        
        # Tasa efectiva anual
        if plazo_meses > 0 and total_aportado > 0:
            # Aproximación de tasa efectiva para anualidades
            periodos_anuales = 12 / plazo_meses
            if periodos_anuales > 0:
                factor_crecimiento = monto_final / total_aportado
                tasa_efectiva = (factor_crecimiento ** periodos_anuales - 1) * 100
            else:
                tasa_efectiva = (rendimiento_total / total_aportado) * 100
        else:
            tasa_efectiva = 0
        
        return {
            'tipo_inversion': 'mensual',
            'monto_mensual': round(monto_mensual, 2),
            'total_aportado': round(total_aportado, 2),
            'rendimiento_total': round(rendimiento_total, 2),
            'monto_final': round(monto_final, 2),
            'tasa_efectiva': round(tasa_efectiva, 2),
            'plazo_meses': plazo_meses,
            'tasa_anual': tasa_anual
        }
        
    except Exception as e:
        raise ValueError(f"Error en cálculo de inversión mensual: {str(e)}")

def generar_tabla_crecimiento_simple(monto_inicial, tasa_anual, plazo_dias):
    """
    Para inversión simple, retorna DataFrame vacío ya que no hay evolución mensual
    """
    return pd.DataFrame()

def generar_tabla_crecimiento_mensual(monto_mensual, tasa_anual, plazo_meses):
    """
    Genera tabla de evolución para inversión mensual
    
    Args:
        monto_mensual (float): Monto mensual
        tasa_anual (float): Tasa anual en porcentaje
        plazo_meses (int): Plazo en meses
    
    Returns:
        pd.DataFrame: Tabla con evolución mes a mes
    """
    try:
        monto_mensual = float(monto_mensual)
        tasa_anual = float(tasa_anual)
        plazo_meses = int(plazo_meses)
        
        tasa_mensual = (tasa_anual / 100) / 12
        
        datos = []
        monto_acumulado = 0
        
        for mes in range(1, plazo_meses + 1):
            # Agregar aportación del mes
            monto_acumulado += monto_mensual
            
            # Calcular rendimiento sobre el saldo acumulado
            rendimiento_mes = monto_acumulado * tasa_mensual
            monto_acumulado += rendimiento_mes
            
            # Totales hasta la fecha
            total_aportado = monto_mensual * mes
            rendimiento_acumulado = monto_acumulado - total_aportado
            
            datos.append({
                'mes': mes,
                'aportacion': monto_mensual,
                'total_aportado': round(total_aportado, 2),
                'rendimiento_mes': round(rendimiento_mes, 2),
                'rendimiento_acumulado': round(rendimiento_acumulado, 2),
                'monto_total': round(monto_acumulado, 2)
            })
        
        return pd.DataFrame(datos)
        
    except Exception as e:
        print(f"Error generando tabla mensual: {e}")
        return pd.DataFrame()

def calcular_comparacion_productos(monto, productos):
    """
    Calcula rendimientos para comparar productos
    Útil para páginas de comparación
    """
    comparaciones = []
    
    for producto_id, producto in productos.items():
        for plazo_dias, plazo_info in producto['plazos'].items():
            try:
                resultado = calcular_inversion_simple(
                    monto, 
                    plazo_info['tasa_anual'], 
                    int(plazo_dias)
                )
                
                comparaciones.append({
                    'producto_id': producto_id,
                    'producto_nombre': producto['nombre'],
                    'plazo_dias': int(plazo_dias),
                    'plazo_nombre': plazo_info['nombre'],
                    'tasa_anual': plazo_info['tasa_anual'],
                    'rendimiento': resultado['rendimiento'],
                    'monto_final': resultado['monto_final'],
                    'tasa_efectiva': resultado['tasa_efectiva']
                })
            except Exception as e:
                print(f"Error calculando {producto_id} - {plazo_dias}: {e}")
                continue
    
    return sorted(comparaciones, key=lambda x: x['rendimiento'], reverse=True)