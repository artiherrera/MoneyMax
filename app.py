from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, make_response
import json
import os
from data.financial_utils import (
    obtener_producto_por_id,
    obtener_tasa_producto,
    calcular_inversion_simple,
    calcular_inversion_mensual,
    generar_tabla_crecimiento_simple,
    generar_tabla_crecimiento_mensual,
    validar_parametros_inversion
)

app = Flask(__name__)
app.secret_key = 'moneymax_secret_key_2024'  # Cambiar en producción

def cargar_productos():
    """Carga productos desde JSON"""
    try:
        with open('data/productos.json', 'r', encoding='utf-8') as f:
            return json.load(f)['productos']
    except FileNotFoundError:
        print("ERROR: No se encontró el archivo productos.json")
        return {}
    except json.JSONDecodeError as e:
        print(f"ERROR: Error al parsear productos.json: {e}")
        return {}

def calcular_badges_automaticos(productos):
    """Calcula automáticamente qué producto tiene la mejor tasa"""
    if not productos:
        return productos
    
    # Encontrar la tasa más alta de todos los productos
    mejor_tasa = 0
    mejor_producto_id = None
    tasas_por_producto = {}
    
    for producto_id, producto in productos.items():
        if 'plazos' not in producto or not producto['plazos']:
            continue
            
        # Encontrar la tasa máxima de este producto
        max_tasa = max(
            float(plazo_info.get('tasa_anual', 0)) 
            for plazo_info in producto['plazos'].values()
        )
        
        tasas_por_producto[producto_id] = max_tasa
        
        if max_tasa > mejor_tasa:
            mejor_tasa = max_tasa
            mejor_producto_id = producto_id
    
    # Limpiar badges existentes y asignar automáticamente
    productos_actualizados = productos.copy()
    
    for producto_id, producto in productos_actualizados.items():
        # Limpiar badge manual existente
        if 'badge' in producto:
            del producto['badge']
        
        # Asignar badges automáticos
        if producto_id == mejor_producto_id:
            producto['badge'] = 'TASA MÁS ALTA'
        elif producto.get('tipo') == 'gubernamental':
            producto['badge'] = 'GOBIERNO'
        # Agregar más lógica de badges aquí si necesitas
    
    return productos_actualizados

@app.route('/')
def index():
    """Página principal con productos"""
    productos_raw = cargar_productos()
    productos = calcular_badges_automaticos(productos_raw)
    return render_template('index.html', productos=productos)

@app.route('/calculator/<producto_id>')
def plazo_selector(producto_id):
    """Página de selección de plazo"""
    productos = cargar_productos()
    
    if producto_id not in productos:
        return render_template('error.html', 
                             mensaje="Producto no encontrado"), 404
    
    producto = productos[producto_id]
    return render_template('plazo_selector.html', 
                         producto=producto, 
                         producto_id=producto_id)

@app.route('/calculator/<producto_id>/<plazo_dias>')
def calculator(producto_id, plazo_dias):
    """Calculadora principal"""
    productos = cargar_productos()
    
    if producto_id not in productos:
        return render_template('error.html', 
                             mensaje="Producto no encontrado"), 404
    
    producto = productos[producto_id]
    
    if plazo_dias not in producto['plazos']:
        return render_template('error.html', 
                             mensaje="Plazo no disponible para este producto"), 404
    
    plazo_info = producto['plazos'][plazo_dias]
    
    return render_template('calculator.html',
                         producto=producto,
                         producto_id=producto_id,
                         plazo_dias=int(plazo_dias),
                         plazo_info=plazo_info,
                         productos_json=json.dumps(productos))

@app.route('/api/calcular', methods=['POST'])
def api_calcular():
    """API para calcular rendimientos"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['monto', 'producto_id', 'plazo_dias', 'tipo_inversion']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Campo requerido: {field}'
                }), 400
        
        monto = float(data['monto'])
        producto_id = data['producto_id']
        plazo_dias = int(data['plazo_dias'])
        tipo_inversion = data['tipo_inversion']
        
        # Validar parámetros
        validacion = validar_parametros_inversion(monto, plazo_dias, producto_id, tipo_inversion)
        if not validacion['valido']:
            return jsonify({
                'error': '; '.join(validacion['errores'])
            }), 400
        
        # Cargar productos
        productos = cargar_productos()
        
        if producto_id not in productos:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        producto = productos[producto_id]
        
        if str(plazo_dias) not in producto['plazos']:
            return jsonify({'error': 'Plazo no disponible'}), 404
        
        # Obtener tasa
        tasa = obtener_tasa_producto(producto, plazo_dias)
        
        if tipo_inversion == 'simple':
            # Inversión única
            resultado = calcular_inversion_simple(monto, tasa, plazo_dias)
            
            return jsonify({
                'tipo_inversion': 'simple',
                'monto_inicial': resultado['monto_inicial'],
                'rendimiento': resultado['rendimiento'],
                'monto_final': resultado['monto_final'],
                'tasa_efectiva': resultado['tasa_efectiva'],
                'plazo_meses': resultado['plazo_meses'],
                'tabla_crecimiento': []  # Vacío para inversión simple
            })
            
        elif tipo_inversion == 'mensual':
            # Inversión mensual
            plazo_meses_corrida = int(data.get('plazo_meses', 12))
            
            resultado = calcular_inversion_mensual(monto, tasa, plazo_meses_corrida)
            tabla = generar_tabla_crecimiento_mensual(monto, tasa, plazo_meses_corrida)
            
            return jsonify({
                'tipo_inversion': 'mensual',
                'monto_mensual': resultado['monto_mensual'],
                'total_aportado': resultado['total_aportado'],
                'rendimiento_total': resultado['rendimiento_total'],
                'monto_final': resultado['monto_final'],
                'tasa_efectiva': resultado['tasa_efectiva'],
                'plazo_meses': resultado['plazo_meses'],
                'tabla_crecimiento': tabla.to_dict('records')
            })
        
        else:
            return jsonify({'error': 'Tipo de inversión no válido'}), 400
            
    except ValueError as e:
        return jsonify({'error': f'Error de formato: {str(e)}'}), 400
    except Exception as e:
        print(f"Error en cálculo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/health')
def health():
    """Endpoint para monitoreo"""
    productos = cargar_productos()
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'productos_cargados': len(productos) > 0,
        'productos_count': len(productos)
    })

@app.route('/robots.txt')
def robots_txt():
    """Servir robots.txt"""
    return send_from_directory('.', 'robots.txt', mimetype='text/plain')

@app.after_request
def after_request(response):
    # Headers de seguridad y SEO
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Robots-Tag'] = 'index, follow'
    
    # Cache para archivos estáticos
    if request.endpoint == 'static':
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 día
    
    return response

@app.route('/sitemap.xml')
def sitemap():
    """Generar sitemap.xml dinámico"""
    # ... código para generar URLs automáticamente

if __name__ == '__main__':
    # Configuración para desarrollo
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
