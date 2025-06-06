from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from data.financial_utils import (
    obtener_producto_por_id,
    obtener_tasa_producto,
    calcular_inversion_simple,
    calcular_inversion_mensual,
    generar_tabla_crecimiento_simple,
    generar_tabla_crecimiento_mensual,
    validar_parametros_inversion,
    formatear_moneda
)

# Crear aplicación Flask
app = Flask(__name__)
app.secret_key = 'moneymax_secret_key_2024'  # Cambiar en producción

# Configuración de desarrollo
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

def cargar_productos():
    """Carga la base de datos de productos desde JSON"""
    try:
        json_path = os.path.join(app.root_path, 'data', 'productos.json')
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('productos', {})
    except FileNotFoundError:
        print("❌ Error: No se encontró data/productos.json")
        return {}
    except json.JSONDecodeError:
        print("❌ Error: productos.json no es válido")
        return {}

def obtener_producto(producto_id):
    """Obtiene un producto específico por ID"""
    productos = cargar_productos()
    return productos.get(producto_id)

@app.route('/')
def index():
    """Landing page con grid de productos"""
    productos = cargar_productos()
    
    if not productos:
        return render_template('error.html', 
                             error="No se pudieron cargar los productos financieros")
    
    return render_template('index.html', productos=productos)

@app.route('/calculator/<producto_id>')
def selector_plazo(producto_id):
    """Página de selección de plazos para un producto"""
    producto = obtener_producto(producto_id)
    
    if not producto:
        return render_template('error.html', 
                             error=f"Producto '{producto_id}' no encontrado")
    
    return render_template('plazo_selector.html', 
                         producto=producto, 
                         producto_id=producto_id)

@app.route('/calculator/<producto_id>/<int:plazo_dias>')
def calculadora(producto_id, plazo_dias):
    """Calculadora para producto y plazo específicos"""
    producto = obtener_producto(producto_id)
    
    if not producto:
        return render_template('error.html', 
                             error=f"Producto '{producto_id}' no encontrado")
    
    # Verificar que el plazo existe
    plazo_str = str(plazo_dias)
    if plazo_str not in producto.get('plazos', {}):
        return render_template('error.html', 
                             error=f"Plazo {plazo_dias} días no disponible para {producto['nombre']}")
    
    plazo_info = producto['plazos'][plazo_str]
    
    return render_template('calculator.html', 
                         producto=producto,
                         producto_id=producto_id,
                         plazo_dias=plazo_dias,
                         plazo_info=plazo_info)

@app.route('/api/calcular', methods=['POST'])
def api_calcular():
    """API endpoint para realizar cálculos financieros"""
    try:
        data = request.get_json()
        print(f"📊 Datos recibidos: {data}")  # Debug
        
        # Extraer parámetros
        producto_id = data.get('producto_id')
        plazo_dias = int(data.get('plazo_dias'))  # Plazo del instrumento
        plazo_meses_corrida = int(data.get('plazo_meses_corrida', plazo_dias // 30))  # Plazo de la corrida
        monto = float(data.get('monto'))
        tipo_inversion = data.get('tipo_inversion', 'simple')
        
        # Obtener producto y validar plazo
        producto = obtener_producto(producto_id)
        if not producto:
            print(f"❌ Producto no encontrado: {producto_id}")
            return jsonify({'error': 'Producto no encontrado'}), 400
        
        plazo_str = str(plazo_dias)
        if plazo_str not in producto.get('plazos', {}):
            print(f"❌ Plazo no disponible: {plazo_dias} para {producto_id}")
            return jsonify({'error': f'Plazo {plazo_dias} días no disponible'}), 400
        
        # Obtener tasa del plazo específico
        tasa = producto['plazos'][plazo_str]['tasa_anual']
        print(f"✅ Tasa aplicada: {tasa}% para {plazo_dias} días, corrida de {plazo_meses_corrida} meses")
        
        # Validar parámetros
        validacion = validar_parametros_inversion(monto, plazo_dias, producto_id)
        if not validacion['valido']:
            print(f"❌ Validación fallida: {validacion['errores']}")
            return jsonify({'error': validacion['errores']}), 400
        
        # Realizar cálculos
        if tipo_inversion == 'simple':
            # Para inversión simple, usar el plazo del instrumento para el cálculo final
            resultado = calcular_inversion_simple(monto, tasa, plazo_dias)
            # Pero generar tabla de crecimiento según el plazo seleccionado
            tabla_crecimiento = generar_tabla_crecimiento_simple(monto, tasa, plazo_meses_corrida * 30)
        else:
            # Para inversión mensual, usar el plazo de corrida seleccionado
            resultado = calcular_inversion_mensual(monto, tasa, plazo_meses_corrida)
            tabla_crecimiento = generar_tabla_crecimiento_mensual(monto, tasa, plazo_meses_corrida)
        
        # Agregar tipo de inversión al resultado
        resultado['tipo_inversion'] = tipo_inversion
        
        # Preparar respuesta
        response = {
            'resultado': resultado,
            'tabla_crecimiento': tabla_crecimiento.to_dict('records'),
            'producto': {
                'nombre': producto['nombre'],
                'tasa': tasa,
                'plazo_dias': plazo_dias,
                'plazo_meses_corrida': plazo_meses_corrida,
                'plazo_nombre': producto['plazos'][plazo_str]['nombre']
            }
        }
        
        print(f"✅ Cálculo exitoso para {producto_id}")
        return jsonify(response)
        
    except ValueError as e:
        print(f"❌ Error de valor: {e}")
        return jsonify({'error': 'Datos inválidos'}), 400
    except Exception as e:
        print(f"❌ Error interno: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/productos')
def api_productos():
    """API endpoint para obtener todos los productos"""
    productos = cargar_productos()
    return jsonify(productos)

@app.route('/api/productos/<producto_id>')
def api_producto(producto_id):
    """API endpoint para obtener un producto específico"""
    producto = obtener_producto(producto_id)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    return jsonify(producto)

@app.errorhandler(404)
def not_found(error):
    """Página de error 404"""
    return render_template('error.html', 
                         error="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    return render_template('error.html', 
                         error="Error interno del servidor"), 500

# Filtros personalizados para templates
@app.template_filter('money')
def money_filter(amount):
    """Filtro para formatear moneda mexicana"""
    return formatear_moneda(amount)

@app.template_filter('percentage')
def percentage_filter(value):
    """Filtro para formatear porcentajes"""
    return f"{value:.2f}%"

# Context processors - variables disponibles en todos los templates
@app.context_processor
def inject_app_info():
    """Inyecta información de la app en todos los templates"""
    return {
        'app_name': 'MoneyMax',
        'app_version': '1.0.0',
        'app_description': 'Calculadora de inversiones mexicanas'
    }

if __name__ == '__main__':
    print("🚀 Iniciando MoneyMax...")
    print("📊 Aplicación de cálculo de inversiones mexicanas")
    print("🌐 Accede en: http://localhost:8000")
    print("=" * 50)
    
    # Verificar que existen los archivos necesarios
    if not os.path.exists('data/productos.json'):
        print("⚠️  Advertencia: data/productos.json no existe")
    
    if not os.path.exists('templates'):
        print("⚠️  Advertencia: carpeta templates no existe")
    
    app.run(host='0.0.0.0', port=8000, debug=True)