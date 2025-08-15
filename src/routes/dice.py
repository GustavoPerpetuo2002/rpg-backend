from flask import Blueprint, request, jsonify
import random
import re

dice_bp = Blueprint('dice', __name__)

def parse_dice_notation(notation):
    """
    Analisa notação de dados (ex: 3d6+2, 1d20, 2d10-1)
    Retorna (quantidade, lados, modificador)
    """
    # Padrão para notação de dados: XdY+Z ou XdY-Z ou XdY
    pattern = r'^(\d+)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, notation.lower().replace(' ', ''))
    
    if not match:
        return None
    
    quantity = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    
    return quantity, sides, modifier

def roll_dice(quantity, sides):
    """Rola uma quantidade de dados com número específico de lados"""
    if quantity <= 0 or sides <= 0:
        return []
    
    if quantity > 100:  # Limite de segurança
        return []
    
    return [random.randint(1, sides) for _ in range(quantity)]

@dice_bp.route('/roll', methods=['POST'])
def roll():
    """Rola dados baseado na notação fornecida"""
    try:
        data = request.get_json()
        
        if not data or 'notation' not in data:
            return jsonify({'error': 'Notação de dados é obrigatória'}), 400
        
        notation = data['notation'].strip()
        
        # Analisar notação
        parsed = parse_dice_notation(notation)
        if not parsed:
            return jsonify({'error': 'Notação de dados inválida. Use formato como: 3d6+2, 1d20, 2d10-1'}), 400
        
        quantity, sides, modifier = parsed
        
        # Validações
        if quantity > 100:
            return jsonify({'error': 'Máximo de 100 dados por rolagem'}), 400
        
        if sides > 1000:
            return jsonify({'error': 'Máximo de 1000 lados por dado'}), 400
        
        # Rolar dados
        rolls = roll_dice(quantity, sides)
        if not rolls:
            return jsonify({'error': 'Erro ao rolar dados'}), 500
        
        # Calcular resultado
        total = sum(rolls) + modifier
        
        return jsonify({
            'notation': notation,
            'rolls': rolls,
            'modifier': modifier,
            'total': total,
            'details': {
                'quantity': quantity,
                'sides': sides,
                'individual_rolls': rolls,
                'sum_of_rolls': sum(rolls),
                'modifier': modifier,
                'final_total': total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@dice_bp.route('/roll-simple', methods=['POST'])
def roll_simple():
    """Rola dados simples (quantidade e lados separados)"""
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data or 'sides' not in data:
            return jsonify({'error': 'Quantidade e lados são obrigatórios'}), 400
        
        quantity = data['quantity']
        sides = data['sides']
        modifier = data.get('modifier', 0)
        
        # Validações
        if not isinstance(quantity, int) or not isinstance(sides, int):
            return jsonify({'error': 'Quantidade e lados devem ser números inteiros'}), 400
        
        if quantity <= 0 or sides <= 0:
            return jsonify({'error': 'Quantidade e lados devem ser positivos'}), 400
        
        if quantity > 100:
            return jsonify({'error': 'Máximo de 100 dados por rolagem'}), 400
        
        if sides > 1000:
            return jsonify({'error': 'Máximo de 1000 lados por dado'}), 400
        
        # Rolar dados
        rolls = roll_dice(quantity, sides)
        if not rolls:
            return jsonify({'error': 'Erro ao rolar dados'}), 500
        
        # Calcular resultado
        total = sum(rolls) + modifier
        
        return jsonify({
            'rolls': rolls,
            'modifier': modifier,
            'total': total,
            'details': {
                'quantity': quantity,
                'sides': sides,
                'individual_rolls': rolls,
                'sum_of_rolls': sum(rolls),
                'modifier': modifier,
                'final_total': total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@dice_bp.route('/roll-multiple', methods=['POST'])
def roll_multiple():
    """Rola múltiplas notações de dados de uma vez"""
    try:
        data = request.get_json()
        
        if not data or 'rolls' not in data:
            return jsonify({'error': 'Lista de rolagens é obrigatória'}), 400
        
        roll_requests = data['rolls']
        
        if not isinstance(roll_requests, list):
            return jsonify({'error': 'Rolagens devem ser uma lista'}), 400
        
        if len(roll_requests) > 20:
            return jsonify({'error': 'Máximo de 20 rolagens por vez'}), 400
        
        results = []
        
        for i, roll_request in enumerate(roll_requests):
            if not isinstance(roll_request, dict) or 'notation' not in roll_request:
                results.append({
                    'index': i,
                    'error': 'Notação é obrigatória',
                    'success': False
                })
                continue
            
            notation = roll_request['notation'].strip()
            label = roll_request.get('label', f'Rolagem {i+1}')
            
            # Analisar notação
            parsed = parse_dice_notation(notation)
            if not parsed:
                results.append({
                    'index': i,
                    'label': label,
                    'notation': notation,
                    'error': 'Notação inválida',
                    'success': False
                })
                continue
            
            quantity, sides, modifier = parsed
            
            # Validações
            if quantity > 100 or sides > 1000:
                results.append({
                    'index': i,
                    'label': label,
                    'notation': notation,
                    'error': 'Limites excedidos',
                    'success': False
                })
                continue
            
            # Rolar dados
            rolls = roll_dice(quantity, sides)
            if not rolls:
                results.append({
                    'index': i,
                    'label': label,
                    'notation': notation,
                    'error': 'Erro ao rolar',
                    'success': False
                })
                continue
            
            # Calcular resultado
            total = sum(rolls) + modifier
            
            results.append({
                'index': i,
                'label': label,
                'notation': notation,
                'rolls': rolls,
                'modifier': modifier,
                'total': total,
                'success': True
            })
        
        return jsonify({
            'results': results,
            'total_rolls': len(results),
            'successful_rolls': len([r for r in results if r.get('success', False)])
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@dice_bp.route('/presets', methods=['GET'])
def get_presets():
    """Retorna presets comuns de dados"""
    presets = {
        'common': [
            {'name': 'D4', 'notation': '1d4', 'description': 'Dado de 4 lados'},
            {'name': 'D6', 'notation': '1d6', 'description': 'Dado comum de 6 lados'},
            {'name': 'D8', 'notation': '1d8', 'description': 'Dado de 8 lados'},
            {'name': 'D10', 'notation': '1d10', 'description': 'Dado de 10 lados'},
            {'name': 'D12', 'notation': '1d12', 'description': 'Dado de 12 lados'},
            {'name': 'D20', 'notation': '1d20', 'description': 'Dado de 20 lados (mais comum em RPGs)'},
            {'name': 'D100', 'notation': '1d100', 'description': 'Dado percentual'}
        ],
        'combat': [
            {'name': 'Ataque Básico', 'notation': '1d20+5', 'description': 'Rolagem de ataque com bônus +5'},
            {'name': 'Dano de Espada', 'notation': '1d8+3', 'description': 'Dano de espada longa'},
            {'name': 'Dano de Arco', 'notation': '1d6+2', 'description': 'Dano de arco curto'},
            {'name': 'Dano Crítico', 'notation': '2d8+6', 'description': 'Dano crítico dobrado'}
        ],
        'attributes': [
            {'name': 'Atributo 3D6', 'notation': '3d6', 'description': 'Geração de atributo padrão'},
            {'name': 'Atributo 4D6', 'notation': '4d6', 'description': 'Geração de atributo (descartar menor)'},
            {'name': 'Teste de Atributo', 'notation': '1d20', 'description': 'Teste contra atributo'}
        ],
        'magic': [
            {'name': 'Bola de Fogo', 'notation': '8d6', 'description': 'Dano de bola de fogo'},
            {'name': 'Míssil Mágico', 'notation': '1d4+1', 'description': 'Dano de míssil mágico'},
            {'name': 'Cura Menor', 'notation': '1d8+1', 'description': 'Cura de poção menor'}
        ]
    }
    
    return jsonify({'presets': presets}), 200

