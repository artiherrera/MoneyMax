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
    Calcula rendimiento para inversión única con interés simple
    
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
        
        # Cálculo de interés simple: I = P * r * t
        # Donde r es la tasa decimal y t es el tiempo en años
        tasa_decimal = tasa_anual / 100
        tiempo_anos = plazo_dias / 365
        
        rendimiento = monto_inicial * tasa_decimal * tiempo_anos
        monto_final = monto_inicial + rendimiento
        
        # Para inversión simple, la tasa efectiva es la misma que la nominal
        # ya que no hay reinversión
        tasa_efectiva = tasa_anual
        
        # Convertir días a meses para mostrar
        plazo_meses = round(plazo_dias / 30.44, 1)
        
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
    Calcula rendimiento para inversión mensual con interés compuesto
    Usa el modelo de anualidad ordinaria vencida
    
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
        
        # Tasa mensual efectiva
        tasa_mensual = (tasa_anual / 100) / 12

        # Valor futuro de anualidad ordinaria: FV = PMT * [((1 + r)^n - 1) / r] * (1 + r)
        if tasa_mensual > 0:
            factor = ((1 + tasa_mensual) ** plazo_meses - 1) / tasa_mensual
            monto_final = monto_mensual * factor * (1 + tasa_mensual)
        else:
            # Si la tasa es 0, es simplemente la suma de aportaciones
            monto_final = monto_mensual * plazo_meses
        
        total_aportado = monto_mensual * plazo_meses
        rendimiento_total = monto_final - total_aportado

        # Intentar calcular TIR real como tasa efectiva anual
        tir_anual = None
        try:
            flujos = [-monto_mensual] * plazo_meses
            flujos[-1] += monto_final
            tir_anual = calcular_tir_anualidad(flujos)
        except:
            pass

        # Si TIR disponible, úsala como tasa efectiva
        if tir_anual is not None:
            tasa_efectiva = round(tir_anual, 2)
        else:
            # Estimación de tasa efectiva
            rendimiento_porcentual = (rendimiento_total / total_aportado) * 100
            if plazo_meses < 12:
                tasa_efectiva = round(rendimiento_porcentual * (12 / plazo_meses), 2)
            else:
                anos = plazo_meses / 12
                tasa_efectiva = round(((monto_final / total_aportado) ** (1/anos) - 1) * 100, 2)

        return {
            'tipo_inversion': 'mensual',
            'monto_mensual': round(monto_mensual, 2),
            'total_aportado': round(total_aportado, 2),
            'rendimiento_total': round(rendimiento_total, 2),
            'monto_final': round(monto_final, 2),
            'tasa_efectiva': tasa_efectiva,
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
    Considera que cada aportación genera intereses desde que se deposita
    
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
        saldo_anterior = 0
        
        for mes in range(1, plazo_meses + 1):
            # Intereses generados por el saldo anterior
            intereses_mes = saldo_anterior * tasa_mensual
            
            # Nuevo saldo = saldo anterior + intereses + nueva aportación
            saldo_actual = saldo_anterior + intereses_mes + monto_mensual
            
            # Totales acumulados
            total_aportado = monto_mensual * mes
            rendimiento_acumulado = saldo_actual - total_aportado
            
            datos.append({
                'mes': mes,
                'aportacion': monto_mensual,
                'total_aportado': round(total_aportado, 2),
                'rendimiento_mes': round(intereses_mes, 2),
                'rendimiento_acumulado': round(rendimiento_acumulado, 2),
                'monto_total': round(saldo_actual, 2)
            })
            
            # Actualizar saldo para siguiente mes
            saldo_anterior = saldo_actual
        
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

# Funciones auxiliares para cálculos más complejos

def calcular_tir_anualidad(flujos_mensuales, valor_presente=0):
    """
    Calcula la Tasa Interna de Retorno (TIR) para una serie de flujos
    Útil para calcular la tasa efectiva real de inversiones mensuales
    """
    try:
        import numpy as np
        from scipy.optimize import newton
        
        def npv(rate, flujos, vp):
            # Valor presente neto
            total = -vp
            for t, flujo in enumerate(flujos, 1):
                total += flujo / ((1 + rate) ** t)
            return total
        
        # Estimación inicial
        tir_mensual = newton(lambda r: npv(r, flujos_mensuales, valor_presente), 0.01)
        tir_anual = (1 + tir_mensual) ** 12 - 1
        
        return tir_anual * 100
    except:
        # Si no está disponible scipy, usar aproximación
        return None

def calcular_valor_presente(monto_futuro, tasa_anual, plazo_dias):
    """
    Calcula el valor presente de un monto futuro
    """
    tasa_decimal = tasa_anual / 100
    tiempo_anos = plazo_dias / 365
    
    valor_presente = monto_futuro / (1 + tasa_decimal * tiempo_anos)
    return round(valor_presente, 2)