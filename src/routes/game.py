from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.character import Character
from src.models.game_session import GameSession
from src.models.npc import NPC
from src.routes.auth import require_auth
from src.ai_config import MASTER_SYSTEM_PROMPT, INTERACTION_PROMPT, AI_TEMPERATURES, MAX_TOKENS
import openai
import json
import random
from datetime import datetime

game_bp = Blueprint('game', __name__)

# Configuração da IA
def get_ai_response(prompt, context="", response_type="medium_response", personality="balanced"):
    """Gera resposta da IA usando OpenAI com configurações realistas"""
    try:
        # Usar o prompt do sistema configurado para máximo realismo
        system_prompt = MASTER_SYSTEM_PROMPT + f"\n\nPersonalidade atual: {personality}\nContexto: {context}"
        
        # Selecionar temperatura baseada no tipo de resposta
        temperature = AI_TEMPERATURES.get('narrative', 0.8)
        if 'dialogue' in response_type:
            temperature = AI_TEMPERATURES['dialogue']
        elif 'consequences' in response_type:
            temperature = AI_TEMPERATURES['consequences']
        
        # Selecionar tokens máximos
        max_tokens = MAX_TOKENS.get(response_type, MAX_TOKENS['medium_response'])

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"A IA está temporariamente indisponível. Erro: {str(e)}"

def generate_npc_action(npc, game_session):
    """Gera uma ação autônoma para um NPC"""
    try:
        npc_context = f"""
        NPC: {npc.name} ({npc.race}, {npc.occupation})
        Personalidade: {', '.join(npc.get_personality_traits())}
        Objetivos de curto prazo: {', '.join(npc.get_goals_short_term())}
        Objetivos de longo prazo: {', '.join(npc.get_goals_long_term())}
        Localização atual: {npc.current_location}
        Atividade atual: {npc.current_activity}
        Humor: {npc.mood}
        Relacionamentos: {json.dumps(npc.get_relationships())}
        
        Contexto do jogo: {game_session.story_context}
        Localização atual da história: {game_session.current_location}
        """
        
        prompt = f"""Baseado no contexto do NPC acima, gere uma ação autônoma realista que este NPC realizaria. 
        
        IMPORTANTE: Este NPC é um ser humano completo com:
        - Desejos, medos, paixões e necessidades reais
        - Motivações complexas e às vezes contraditórias  
        - Capacidade para todas as emoções e ações humanas
        - Relacionamentos e conflitos pessoais
        - Ambições, segredos e vulnerabilidades
        
        A ação deve ser:
        - Completamente consistente com sua personalidade e situação
        - Realista para um ser humano em um mundo medieval
        - Potencialmente surpreendente mas sempre lógica
        - Capaz de criar novas oportunidades de interação
        
        Responda apenas com a descrição da ação em 2-3 frases detalhadas."""
        
        action = get_ai_response(prompt, npc_context, "detailed_scene", "creative")
        
        # Registrar a ação na memória do NPC
        npc.add_memory(f"Ação autônoma: {action}")
        npc.last_interaction = datetime.utcnow()
        
        return action
    except Exception as e:
        return f"{npc.name} continua suas atividades normais, perdido em pensamentos sobre seus próprios desejos e preocupações."

@game_bp.route('/sessions', methods=['GET'])
@require_auth
def get_game_sessions():
    """Lista todas as sessões de jogo do usuário"""
    try:
        user_id = session['user_id']
        sessions = GameSession.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'sessions': [s.to_dict() for s in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@game_bp.route('/sessions', methods=['POST'])
@require_auth
def create_game_session():
    """Cria uma nova sessão de jogo"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        # Validações
        if not data.get('session_name') or not data.get('character_id'):
            return jsonify({'error': 'Nome da sessão e ID do personagem são obrigatórios'}), 400
        
        # Verificar se o personagem pertence ao usuário
        character = Character.query.filter_by(id=data['character_id'], user_id=user_id).first()
        if not character:
            return jsonify({'error': 'Personagem não encontrado'}), 404
        
        # Criar sessão
        game_session = GameSession(
            user_id=user_id,
            character_id=data['character_id'],
            session_name=data['session_name'],
            world_setting=data.get('world_setting', 'fantasy'),
            difficulty_level=data.get('difficulty_level', 'normal'),
            ai_personality=data.get('ai_personality', 'balanced'),
            ai_difficulty=data.get('ai_difficulty', 'normal')
        )
        
        db.session.add(game_session)
        db.session.commit()
        
        # Gerar introdução inicial
        intro_prompt = f"""Crie uma introdução para uma nova aventura de RPG.
        Personagem: {character.name} (Nível {character.level} {character.race} {character.character_class})
        Configuração: {game_session.world_setting}
        Dificuldade: {game_session.difficulty_level}
        
        Crie uma cena inicial interessante que estabeleça o cenário e apresente o primeiro desafio ou oportunidade."""
        
        intro_story = get_ai_response(intro_prompt, "", game_session.ai_personality)
        
        # Atualizar sessão com a introdução
        game_session.current_scene = intro_story
        game_session.story_context = f"Aventura iniciada com {character.name}"
        game_session.add_story_entry("narration", intro_story)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sessão de jogo criada com sucesso',
            'session': game_session.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@game_bp.route('/sessions/<int:session_id>', methods=['GET'])
@require_auth
def get_game_session(session_id):
    """Retorna uma sessão de jogo específica"""
    try:
        user_id = session['user_id']
        game_session = GameSession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not game_session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        return jsonify({'session': game_session.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@game_bp.route('/sessions/<int:session_id>/action', methods=['POST'])
@require_auth
def player_action(session_id):
    """Processa uma ação do jogador"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        if not data.get('action'):
            return jsonify({'error': 'Ação é obrigatória'}), 400
        
        game_session = GameSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not game_session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        player_action_text = data['action']
        
        # Registrar ação do jogador
        game_session.add_player_action(player_action_text)
        game_session.add_story_entry("player_action", player_action_text, "Jogador")
        
        # Gerar resposta da IA
        context = f"""
        Contexto da história: {game_session.story_context}
        Cena atual: {game_session.current_scene}
        Localização: {game_session.current_location}
        Últimas entradas do log: {json.dumps(game_session.get_story_log()[-5:])}
        """
        
        ai_prompt = f"""O jogador realizou a seguinte ação: "{player_action_text}"
        
        Como Mestre de RPG, responda a esta ação:
        1. Descreva o resultado da ação
        2. Avance a narrativa
        3. Apresente a nova situação
        4. Ofereça opções ou desafios para o próximo movimento
        
        Mantenha a resposta envolvente e entre 100-200 palavras."""
        
        ai_response = get_ai_response(ai_prompt, context, game_session.ai_personality)
        
        # Registrar resposta da IA
        game_session.add_story_entry("narration", ai_response)
        game_session.current_scene = ai_response
        game_session.last_played = datetime.utcnow()
        
        # Processar ações autônomas dos NPCs (chance de 30%)
        npc_actions = []
        if random.random() < 0.3:
            npcs = NPC.query.filter_by(game_session_id=session_id).all()
            for npc in npcs[:2]:  # Máximo 2 NPCs por turno
                if random.random() < 0.5:  # 50% de chance para cada NPC
                    npc_action = generate_npc_action(npc, game_session)
                    npc_actions.append({
                        'npc_name': npc.name,
                        'action': npc_action
                    })
                    game_session.add_story_entry("npc_action", npc_action, npc.name)
        
        db.session.commit()
        
        return jsonify({
            'ai_response': ai_response,
            'npc_actions': npc_actions,
            'session': game_session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@game_bp.route('/sessions/<int:session_id>/npcs', methods=['GET'])
@require_auth
def get_session_npcs(session_id):
    """Lista NPCs de uma sessão"""
    try:
        user_id = session['user_id']
        game_session = GameSession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not game_session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        npcs = NPC.query.filter_by(game_session_id=session_id).all()
        
        return jsonify({
            'npcs': [npc.to_dict() for npc in npcs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@game_bp.route('/sessions/<int:session_id>/npcs', methods=['POST'])
@require_auth
def create_npc(session_id):
    """Cria um novo NPC para a sessão"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        game_session = GameSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not game_session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        if not data.get('name'):
            return jsonify({'error': 'Nome do NPC é obrigatório'}), 400
        
        # Criar NPC
        npc = NPC(
            game_session_id=session_id,
            name=data['name'],
            race=data.get('race', 'human'),
            occupation=data.get('occupation', ''),
            current_location=data.get('current_location', game_session.current_location),
            current_activity=data.get('current_activity', 'Explorando'),
            physical_description=data.get('physical_description', ''),
            clothing_description=data.get('clothing_description', '')
        )
        
        # Definir atributos
        if 'attributes' in data:
            for attr, value in data['attributes'].items():
                if hasattr(npc, attr):
                    setattr(npc, attr, value)
        
        # Definir personalidade
        if 'personality_traits' in data:
            npc.set_personality_traits(data['personality_traits'])
        
        if 'goals_short_term' in data:
            npc.set_goals_short_term(data['goals_short_term'])
        
        if 'goals_long_term' in data:
            npc.set_goals_long_term(data['goals_long_term'])
        
        if 'fears' in data:
            npc.set_fears(data['fears'])
        
        db.session.add(npc)
        db.session.commit()
        
        return jsonify({
            'message': 'NPC criado com sucesso',
            'npc': npc.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@game_bp.route('/sessions/<int:session_id>/save', methods=['POST'])
@require_auth
def save_game(session_id):
    """Salva o estado atual do jogo"""
    try:
        user_id = session['user_id']
        game_session = GameSession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not game_session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        # Atualizar timestamp de última jogada
        game_session.last_played = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Jogo salvo com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@game_bp.route('/sessions/<int:session_id>/npcs/update-all', methods=['POST'])
@require_auth
def update_all_npcs(session_id):
    """Atualiza todos os NPCs da sessão (evolução autônoma)"""
    try:
        user_id = session['user_id']
        game_session = GameSession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not game_session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        npcs = NPC.query.filter_by(game_session_id=session_id).all()
        updates = []
        
        for npc in npcs:
            # Simular evolução do NPC
            if random.random() < 0.1:  # 10% de chance de ganhar skill points
                npc.skill_points += 1
            
            if random.random() < 0.05:  # 5% de chance de aprender nova habilidade
                new_skills = ["Observação", "Persuasão", "Furtividade", "Combate", "Magia", "Artesanato"]
                available_skills = [s for s in new_skills if s not in npc.get_learned_skills()]
                if available_skills:
                    new_skill = random.choice(available_skills)
                    npc.add_skill(new_skill)
                    updates.append(f"{npc.name} aprendeu {new_skill}")
            
            # Atualizar humor baseado em eventos recentes
            moods = ["feliz", "neutro", "triste", "irritado", "animado", "pensativo"]
            if random.random() < 0.2:  # 20% de chance de mudança de humor
                npc.mood = random.choice(moods)
                updates.append(f"{npc.name} está se sentindo {npc.mood}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'NPCs atualizados com sucesso',
            'updates': updates
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

