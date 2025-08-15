from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.character import Character
from src.routes.auth import require_auth

character_bp = Blueprint('character', __name__)

# Dados de referência para criação de personagem
RACES = {
    'human': {
        'name': 'Humano',
        'bonuses': {'strength': 1, 'dexterity': 1, 'constitution': 1, 'intelligence': 1, 'wisdom': 1, 'charisma': 1},
        'description': 'Versáteis e adaptáveis, os humanos são a raça mais comum.',
        'racial_advantages': [
            {
                'name': 'Versatilidade Humana',
                'description': 'Pode escolher uma habilidade extra de qualquer classe',
                'cost': 0
            },
            {
                'name': 'Determinação',
                'description': '+2 em testes de resistência mental',
                'cost': 0
            }
        ],
        'racial_disadvantages': [
            {
                'name': 'Vida Curta',
                'description': 'Envelhece mais rapidamente que outras raças',
                'points': 1
            }
        ]
    },
    'elf': {
        'name': 'Elfo',
        'bonuses': {'dexterity': 2, 'intelligence': 1, 'wisdom': 1},
        'description': 'Ágeis e sábios, os elfos possuem longa vida e afinidade com magia.',
        'racial_advantages': [
            {
                'name': 'Visão Élfica',
                'description': 'Enxerga perfeitamente no escuro até 30 metros',
                'cost': 0
            },
            {
                'name': 'Resistência à Magia',
                'description': '+3 em testes contra magias de encantamento',
                'cost': 0
            },
            {
                'name': 'Afinidade Arcana',
                'description': '+2 em todos os testes relacionados à magia',
                'cost': 0
            }
        ],
        'racial_disadvantages': [
            {
                'name': 'Arrogância Élfica',
                'description': 'Dificuldade em aceitar conselhos de outras raças',
                'points': 2
            },
            {
                'name': 'Sensibilidade ao Ferro',
                'description': '-1 em testes quando em contato direto com ferro',
                'points': 1
            }
        ]
    },
    'dwarf': {
        'name': 'Anão',
        'bonuses': {'strength': 2, 'constitution': 2},
        'description': 'Resistentes e fortes, os anões são mestres em artesanato e combate.',
        'racial_advantages': [
            {
                'name': 'Resistência Anã',
                'description': 'Resistência a venenos e doenças (+4 em testes)',
                'cost': 0
            },
            {
                'name': 'Visão no Escuro',
                'description': 'Enxerga no escuro até 20 metros',
                'cost': 0
            },
            {
                'name': 'Maestria em Forja',
                'description': '+3 em testes de artesanato com metal e pedra',
                'cost': 0
            }
        ],
        'racial_disadvantages': [
            {
                'name': 'Baixa Estatura',
                'description': 'Velocidade reduzida e dificuldade para alcançar objetos altos',
                'points': 2
            },
            {
                'name': 'Teimosia',
                'description': 'Dificuldade em mudar de opinião ou aceitar novas ideias',
                'points': 1
            }
        ]
    },
    'halfling': {
        'name': 'Halfling',
        'bonuses': {'dexterity': 2, 'charisma': 1},
        'description': 'Pequenos mas corajosos, os halflings são conhecidos por sua sorte.',
        'racial_advantages': [
            {
                'name': 'Sorte Halfling',
                'description': 'Pode rolar novamente qualquer 1 natural uma vez por teste',
                'cost': 0
            },
            {
                'name': 'Pés Peludos',
                'description': '+3 em testes de movimento silencioso',
                'cost': 0
            },
            {
                'name': 'Coragem Natural',
                'description': '+2 em testes contra medo',
                'cost': 0
            }
        ],
        'racial_disadvantages': [
            {
                'name': 'Tamanho Pequeno',
                'description': '-2 em testes de força e alcance limitado',
                'points': 2
            },
            {
                'name': 'Curiosidade Excessiva',
                'description': 'Dificuldade em resistir a explorar lugares perigosos',
                'points': 1
            }
        ]
    },
    'orc': {
        'name': 'Orc',
        'bonuses': {'strength': 3, 'constitution': 1},
        'penalties': {'intelligence': -1, 'charisma': -1},
        'description': 'Poderosos e selvagens, os orcs são guerreiros natos.',
        'racial_advantages': [
            {
                'name': 'Fúria Orca',
                'description': '+2 em ataques quando ferido (abaixo de 50% da vida)',
                'cost': 0
            },
            {
                'name': 'Resistência à Dor',
                'description': 'Ignora penalidades de ferimentos leves',
                'cost': 0
            },
            {
                'name': 'Visão Noturna',
                'description': 'Enxerga no escuro até 15 metros',
                'cost': 0
            }
        ],
        'racial_disadvantages': [
            {
                'name': 'Temperamento Explosivo',
                'description': 'Dificuldade em controlar a raiva em situações tensas',
                'points': 2
            },
            {
                'name': 'Preconceito Social',
                'description': '-2 em testes sociais com raças civilizadas',
                'points': 2
            },
            {
                'name': 'Sensibilidade à Luz',
                'description': '-1 em testes sob luz solar intensa',
                'points': 1
            }
        ]
    },
    'dragonborn': {
        'name': 'Draconato',
        'bonuses': {'strength': 2, 'charisma': 1, 'constitution': 1},
        'description': 'Descendentes de dragões, orgulhosos e poderosos.',
        'racial_advantages': [
            {
                'name': 'Sopro Dracônico',
                'description': 'Pode usar sopro de fogo uma vez por combate (dano baseado no nível)',
                'cost': 0
            },
            {
                'name': 'Escamas Dracônicas',
                'description': '+1 de armadura natural',
                'cost': 0
            },
            {
                'name': 'Resistência ao Fogo',
                'description': 'Metade do dano de ataques de fogo',
                'cost': 0
            }
        ],
        'racial_disadvantages': [
            {
                'name': 'Orgulho Dracônico',
                'description': 'Dificuldade em recuar ou admitir derrota',
                'points': 2
            },
            {
                'name': 'Aparência Intimidadora',
                'description': '-2 em testes sociais iniciais com desconhecidos',
                'points': 1
            }
        ]
    },
    'tiefling': {
        'name': 'Tiefling',
        'bonuses': {'charisma': 2, 'intelligence': 1},
        'description': 'Com sangue infernal, são temidos mas poderosos.',
        'racial_advantages': [
            {
                'name': 'Herança Infernal',
                'description': 'Pode usar magias menores de fogo e escuridão',
                'cost': 0
            },
            {
                'name': 'Resistência ao Fogo',
                'description': 'Metade do dano de ataques de fogo',
                'cost': 0
            },
            {
                'name': 'Visão no Escuro',
                'description': 'Enxerga no escuro até 25 metros',
                'cost': 0
            }
        ],
        'racial_disadvantages': [
            {
                'name': 'Marca Infernal',
                'description': 'Aparência demoníaca causa medo e preconceito',
                'points': 3
            },
            {
                'name': 'Tentações Sombrias',
                'description': 'Vulnerável a influências malignas',
                'points': 2
            }
        ]
    }
}

CLASSES = {
    'warrior': {
        'name': 'Guerreiro',
        'primary_attributes': ['strength', 'constitution'],
        'hp_bonus': 10,
        'mp_bonus': 0,
        'description': 'Especialista em combate corpo a corpo e uso de armas.'
    },
    'mage': {
        'name': 'Mago',
        'primary_attributes': ['intelligence', 'wisdom'],
        'hp_bonus': 0,
        'mp_bonus': 15,
        'description': 'Mestre das artes arcanas e magias poderosas.'
    },
    'rogue': {
        'name': 'Ladino',
        'primary_attributes': ['dexterity', 'charisma'],
        'hp_bonus': 5,
        'mp_bonus': 5,
        'description': 'Especialista em furtividade, agilidade e habilidades sociais.'
    },
    'cleric': {
        'name': 'Clérigo',
        'primary_attributes': ['wisdom', 'charisma'],
        'hp_bonus': 7,
        'mp_bonus': 10,
        'description': 'Servo divino com poderes de cura e proteção.'
    },
    'ranger': {
        'name': 'Patrulheiro',
        'primary_attributes': ['dexterity', 'wisdom'],
        'hp_bonus': 8,
        'mp_bonus': 3,
        'description': 'Explorador da natureza com habilidades de rastreamento e tiro.'
    }
}

ADVANTAGES = [
    {'id': 'night_vision', 'name': 'Visão Noturna', 'cost': 2, 'description': 'Pode ver no escuro como se fosse dia.'},
    {'id': 'lucky', 'name': 'Sortudo', 'cost': 3, 'description': 'Pode rolar novamente um dado por sessão.'},
    {'id': 'strong_will', 'name': 'Força de Vontade', 'cost': 2, 'description': '+2 em resistência mental.'},
    {'id': 'fast_learner', 'name': 'Aprendizado Rápido', 'cost': 3, 'description': 'Ganha experiência 25% mais rápido.'},
    {'id': 'charismatic', 'name': 'Carismático', 'cost': 2, 'description': '+2 em todas as interações sociais.'},
    {'id': 'tough', 'name': 'Resistente', 'cost': 2, 'description': '+5 pontos de vida adicionais.'},
    {'id': 'magical_affinity', 'name': 'Afinidade Mágica', 'cost': 3, 'description': '+3 pontos de mana adicionais.'}
]

DISADVANTAGES = [
    {'id': 'fear_heights', 'name': 'Medo de Altura', 'points': 1, 'description': 'Penalidade em situações de altura.'},
    {'id': 'bad_luck', 'name': 'Azar', 'points': 2, 'description': 'Falhas críticas são mais prováveis.'},
    {'id': 'weak_constitution', 'name': 'Constituição Fraca', 'points': 2, 'description': '-3 pontos de vida.'},
    {'id': 'antisocial', 'name': 'Antissocial', 'points': 1, 'description': 'Penalidade em interações sociais.'},
    {'id': 'slow_learner', 'name': 'Aprendizado Lento', 'points': 2, 'description': 'Ganha experiência 25% mais devagar.'},
    {'id': 'magic_resistance', 'name': 'Resistência à Magia', 'points': 1, 'description': 'Dificuldade para usar e ser afetado por magia.'},
    {'id': 'phobia', 'name': 'Fobia', 'points': 1, 'description': 'Medo extremo de algo específico.'}
]

@character_bp.route('/reference-data', methods=['GET'])
def get_reference_data():
    """Retorna dados de referência para criação de personagem"""
    return jsonify({
        'races': RACES,
        'classes': CLASSES,
        'advantages': ADVANTAGES,
        'disadvantages': DISADVANTAGES
    }), 200

@character_bp.route('/', methods=['GET'])
@require_auth
def get_characters():
    """Lista todos os personagens do usuário"""
    try:
        user_id = session['user_id']
        characters = Character.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'characters': [char.to_dict() for char in characters]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@character_bp.route('/<int:character_id>', methods=['GET'])
@require_auth
def get_character(character_id):
    """Retorna um personagem específico"""
    try:
        user_id = session['user_id']
        character = Character.query.filter_by(id=character_id, user_id=user_id).first()
        
        if not character:
            return jsonify({'error': 'Personagem não encontrado'}), 404
        
        return jsonify({'character': character.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@character_bp.route('/', methods=['POST'])
@require_auth
def create_character():
    """Cria um novo personagem"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        # Validações básicas
        required_fields = ['name', 'race', 'character_class']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Validar raça e classe
        if data['race'] not in RACES:
            return jsonify({'error': 'Raça inválida'}), 400
        
        if data['character_class'] not in CLASSES:
            return jsonify({'error': 'Classe inválida'}), 400
        
        # Calcular atributos base
        base_attributes = {
            'strength': 10,
            'dexterity': 10,
            'constitution': 10,
            'intelligence': 10,
            'wisdom': 10,
            'charisma': 10
        }
        
        # Aplicar bônus raciais
        race_data = RACES[data['race']]
        if 'bonuses' in race_data:
            for attr, bonus in race_data['bonuses'].items():
                base_attributes[attr] += bonus
        
        if 'penalties' in race_data:
            for attr, penalty in race_data['penalties'].items():
                base_attributes[attr] += penalty
        
        # Aplicar pontos distribuídos pelo jogador
        if 'attribute_points' in data:
            for attr, points in data['attribute_points'].items():
                if attr in base_attributes:
                    base_attributes[attr] += points
        
        # Calcular HP e MP baseado na classe
        class_data = CLASSES[data['character_class']]
        base_hp = 10 + base_attributes['constitution'] + class_data['hp_bonus']
        base_mp = 10 + base_attributes['intelligence'] + class_data['mp_bonus']
        
        # Criar personagem
        character = Character(
            user_id=user_id,
            name=data['name'],
            race=data['race'],
            character_class=data['character_class'],
            strength=base_attributes['strength'],
            dexterity=base_attributes['dexterity'],
            constitution=base_attributes['constitution'],
            intelligence=base_attributes['intelligence'],
            wisdom=base_attributes['wisdom'],
            charisma=base_attributes['charisma'],
            current_hp=base_hp,
            max_hp=base_hp,
            current_mp=base_mp,
            max_mp=base_mp,
            background=data.get('background', ''),
            notes=data.get('notes', '')
        )
        
        # Adicionar vantagens e desvantagens
        if 'advantages' in data:
            character.set_advantages(data['advantages'])
        
        if 'disadvantages' in data:
            character.set_disadvantages(data['disadvantages'])
        
        db.session.add(character)
        db.session.commit()
        
        return jsonify({
            'message': 'Personagem criado com sucesso',
            'character': character.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@character_bp.route('/<int:character_id>', methods=['PUT'])
@require_auth
def update_character(character_id):
    """Atualiza um personagem"""
    try:
        user_id = session['user_id']
        character = Character.query.filter_by(id=character_id, user_id=user_id).first()
        
        if not character:
            return jsonify({'error': 'Personagem não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos permitidos
        updatable_fields = [
            'name', 'background', 'notes', 'current_hp', 'current_mp',
            'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(character, field, data[field])
        
        # Atualizar vantagens e desvantagens
        if 'advantages' in data:
            character.set_advantages(data['advantages'])
        
        if 'disadvantages' in data:
            character.set_disadvantages(data['disadvantages'])
        
        if 'equipment' in data:
            character.set_equipment(data['equipment'])
        
        if 'inventory' in data:
            character.set_inventory(data['inventory'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Personagem atualizado com sucesso',
            'character': character.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@character_bp.route('/<int:character_id>', methods=['DELETE'])
@require_auth
def delete_character(character_id):
    """Deleta um personagem"""
    try:
        user_id = session['user_id']
        character = Character.query.filter_by(id=character_id, user_id=user_id).first()
        
        if not character:
            return jsonify({'error': 'Personagem não encontrado'}), 404
        
        db.session.delete(character)
        db.session.commit()
        
        return jsonify({'message': 'Personagem deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

