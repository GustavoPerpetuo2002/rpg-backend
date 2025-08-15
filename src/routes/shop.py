from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.character import Character
from src.routes.auth import require_auth
import openai
import json
import random

shop_bp = Blueprint('shop', __name__)

def generate_shop_items(location, character_level, shop_type="general"):
    """Gera itens para a loja baseado na localização e nível do personagem"""
    try:
        prompt = f"""Você é um mestre de RPG criando uma loja em um mundo de fantasia medieval.

Localização: {location}
Nível do personagem: {character_level}
Tipo de loja: {shop_type}

Crie 8-12 itens únicos e interessantes para esta loja. Os itens devem ser apropriados para:
- A localização (ex: itens mágicos em torres de magos, armas em forges, poções em alquimistas)
- O nível do personagem (itens mais poderosos para níveis maiores)
- O ambiente medieval fantástico

Para cada item, forneça:
- Nome criativo e temático
- Descrição detalhada (2-3 frases)
- Tipo (weapon, armor, potion, scroll, misc, accessory)
- Preço em moedas de ouro (balanceado para o nível)
- Raridade (common, uncommon, rare, epic, legendary)
- Propriedades especiais (se houver)

Responda APENAS com um JSON válido no formato:
{{
  "items": [
    {{
      "name": "Nome do Item",
      "description": "Descrição detalhada do item",
      "type": "weapon",
      "price": 150,
      "rarity": "uncommon",
      "properties": {{
        "damage": "+2",
        "special": "Brilha na escuridão"
      }}
    }}
  ]
}}"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um especialista em criar itens de RPG medieval fantástico. Responda sempre com JSON válido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        
        content = response.choices[0].message.content.strip()
        
        # Tentar extrair JSON da resposta
        try:
            # Procurar por JSON na resposta
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: itens padrão se a IA falhar
        return generate_fallback_items(location, character_level, shop_type)
        
    except Exception as e:
        print(f"Erro ao gerar itens da loja: {e}")
        return generate_fallback_items(location, character_level, shop_type)

def generate_fallback_items(location, character_level, shop_type):
    """Gera itens padrão caso a IA falhe"""
    base_items = [
        {
            "name": "Espada de Ferro",
            "description": "Uma espada bem forjada de ferro puro. Confiável e afiada.",
            "type": "weapon",
            "price": 50 + (character_level * 10),
            "rarity": "common",
            "properties": {"damage": "+1", "durability": "Alta"}
        },
        {
            "name": "Poção de Cura Menor",
            "description": "Uma poção vermelha que restaura vitalidade. Sabor de frutas vermelhas.",
            "type": "potion",
            "price": 25 + (character_level * 5),
            "rarity": "common",
            "properties": {"healing": "1d8+2", "uses": "1"}
        },
        {
            "name": "Armadura de Couro",
            "description": "Armadura leve feita de couro curtido. Oferece proteção básica.",
            "type": "armor",
            "price": 75 + (character_level * 15),
            "rarity": "common",
            "properties": {"defense": "+2", "weight": "Leve"}
        },
        {
            "name": "Pergaminho de Luz",
            "description": "Um pergaminho que emite uma luz suave quando ativado.",
            "type": "scroll",
            "price": 30 + (character_level * 8),
            "rarity": "uncommon",
            "properties": {"spell": "Luz", "duration": "1 hora"}
        },
        {
            "name": "Anel de Proteção",
            "description": "Um anel simples que oferece proteção mágica contra ataques menores.",
            "type": "accessory",
            "price": 100 + (character_level * 20),
            "rarity": "uncommon",
            "properties": {"defense": "+1", "magic_resistance": "5%"}
        },
        {
            "name": "Corda Élfica",
            "description": "Corda leve e resistente feita pelos elfos. Nunca se desgasta.",
            "type": "misc",
            "price": 40 + (character_level * 5),
            "rarity": "uncommon",
            "properties": {"length": "15 metros", "special": "Indestrutível"}
        }
    ]
    
    # Adicionar variação baseada na localização
    location_modifiers = {
        "vila": 0.8,
        "cidade": 1.0,
        "capital": 1.5,
        "torre": 1.3,
        "dungeon": 1.2,
        "floresta": 0.9
    }
    
    modifier = 1.0
    for loc_key, mod_value in location_modifiers.items():
        if loc_key.lower() in location.lower():
            modifier = mod_value
            break
    
    # Aplicar modificador de preço
    for item in base_items:
        item["price"] = int(item["price"] * modifier)
    
    return {"items": base_items}

@shop_bp.route('/generate', methods=['POST'])
@require_auth
def generate_shop():
    """Gera uma loja baseada na localização do personagem"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        character_id = data.get('character_id')
        shop_type = data.get('shop_type', 'general')
        
        if not character_id:
            return jsonify({'error': 'ID do personagem é obrigatório'}), 400
        
        # Buscar personagem
        character = Character.query.filter_by(id=character_id, user_id=user_id).first()
        if not character:
            return jsonify({'error': 'Personagem não encontrado'}), 404
        
        # Gerar itens da loja
        shop_data = generate_shop_items(
            character.current_location, 
            character.level, 
            shop_type
        )
        
        return jsonify({
            'shop': {
                'location': character.current_location,
                'type': shop_type,
                'items': shop_data.get('items', []),
                'generated_at': 'now'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@shop_bp.route('/buy', methods=['POST'])
@require_auth
def buy_item():
    """Compra um item da loja"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        character_id = data.get('character_id')
        item_data = data.get('item')
        quantity = data.get('quantity', 1)
        
        if not character_id or not item_data:
            return jsonify({'error': 'ID do personagem e dados do item são obrigatórios'}), 400
        
        # Buscar personagem
        character = Character.query.filter_by(id=character_id, user_id=user_id).first()
        if not character:
            return jsonify({'error': 'Personagem não encontrado'}), 404
        
        total_cost = item_data['price'] * quantity
        
        # Verificar se tem ouro suficiente
        if not character.can_afford(total_cost):
            return jsonify({'error': f'Ouro insuficiente. Necessário: {total_cost}, Disponível: {character.gold}'}), 400
        
        # Realizar compra
        character.spend_gold(total_cost)
        
        # Adicionar item ao inventário
        purchase_item = item_data.copy()
        purchase_item['quantity'] = quantity
        character.add_item_to_inventory(purchase_item)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Item {item_data["name"]} comprado com sucesso!',
            'character': character.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@shop_bp.route('/sell', methods=['POST'])
@require_auth
def sell_item():
    """Vende um item do inventário"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        character_id = data.get('character_id')
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        if not character_id or not item_id:
            return jsonify({'error': 'ID do personagem e ID do item são obrigatórios'}), 400
        
        # Buscar personagem
        character = Character.query.filter_by(id=character_id, user_id=user_id).first()
        if not character:
            return jsonify({'error': 'Personagem não encontrado'}), 404
        
        # Encontrar item no inventário
        inventory = character.get_inventory()
        item_to_sell = None
        
        for item in inventory:
            if item['id'] == item_id:
                item_to_sell = item
                break
        
        if not item_to_sell:
            return jsonify({'error': 'Item não encontrado no inventário'}), 404
        
        if item_to_sell['quantity'] < quantity:
            return jsonify({'error': 'Quantidade insuficiente no inventário'}), 400
        
        # Calcular valor de venda (50% do valor original)
        sell_price = int(item_to_sell.get('value', item_to_sell.get('price', 0)) * 0.5)
        total_earned = sell_price * quantity
        
        # Realizar venda
        character.remove_item_from_inventory(item_id, quantity)
        character.earn_gold(total_earned)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Item {item_to_sell["name"]} vendido por {total_earned} moedas de ouro!',
            'character': character.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@shop_bp.route('/types', methods=['GET'])
def get_shop_types():
    """Retorna os tipos de loja disponíveis"""
    shop_types = {
        'general': {
            'name': 'Loja Geral',
            'description': 'Variedade de itens básicos e úteis',
            'icon': '🏪'
        },
        'blacksmith': {
            'name': 'Ferraria',
            'description': 'Armas e armaduras de qualidade',
            'icon': '⚒️'
        },
        'alchemist': {
            'name': 'Alquimista',
            'description': 'Poções, pergaminhos e componentes mágicos',
            'icon': '🧪'
        },
        'magic_shop': {
            'name': 'Loja Mágica',
            'description': 'Itens encantados e artefatos místicos',
            'icon': '🔮'
        },
        'tavern': {
            'name': 'Taverna',
            'description': 'Comida, bebida e informações',
            'icon': '🍺'
        },
        'temple': {
            'name': 'Templo',
            'description': 'Bênçãos, cura e itens sagrados',
            'icon': '⛪'
        }
    }
    
    return jsonify({'shop_types': shop_types}), 200

