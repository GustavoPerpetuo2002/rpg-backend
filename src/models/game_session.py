from src.models.user import db
import json
from datetime import datetime

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    
    # Informações da sessão
    session_name = db.Column(db.String(200), nullable=False)
    world_setting = db.Column(db.String(100), default='fantasy')  # fantasy, sci-fi, modern, etc.
    difficulty_level = db.Column(db.String(20), default='normal')  # easy, normal, hard, extreme
    
    # Estado atual da história
    current_scene = db.Column(db.Text, default='')
    current_location = db.Column(db.String(200), default='')
    story_context = db.Column(db.Text, default='')
    
    # Histórico da aventura
    story_log = db.Column(db.Text, default='[]')           # JSON array de eventos da história
    player_actions = db.Column(db.Text, default='[]')      # JSON array de ações do jogador
    
    # Estado do mundo
    world_state = db.Column(db.Text, default='{}')         # JSON object com estado geral do mundo
    active_quests = db.Column(db.Text, default='[]')       # JSON array de missões ativas
    completed_quests = db.Column(db.Text, default='[]')    # JSON array de missões completadas
    
    # Configurações da IA
    ai_personality = db.Column(db.String(50), default='balanced')  # creative, balanced, logical
    ai_difficulty = db.Column(db.String(20), default='normal')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_played = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    npcs = db.relationship('NPC', backref='game_session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<GameSession {self.session_name}>'
    
    def get_story_log(self):
        return json.loads(self.story_log) if self.story_log else []
    
    def add_story_entry(self, entry_type, content, character_name=None):
        """Adiciona uma entrada ao log da história"""
        story_entries = self.get_story_log()
        story_entries.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': entry_type,  # 'narration', 'player_action', 'npc_dialogue', 'system'
            'content': content,
            'character': character_name
        })
        self.story_log = json.dumps(story_entries)
    
    def get_player_actions(self):
        return json.loads(self.player_actions) if self.player_actions else []
    
    def add_player_action(self, action_description, result=None):
        """Adiciona uma ação do jogador"""
        actions = self.get_player_actions()
        actions.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': action_description,
            'result': result
        })
        self.player_actions = json.dumps(actions)
    
    def get_world_state(self):
        return json.loads(self.world_state) if self.world_state else {}
    
    def update_world_state(self, key, value):
        """Atualiza um aspecto do estado do mundo"""
        world_state = self.get_world_state()
        world_state[key] = value
        self.world_state = json.dumps(world_state)
    
    def get_active_quests(self):
        return json.loads(self.active_quests) if self.active_quests else []
    
    def add_quest(self, quest_data):
        """Adiciona uma nova missão"""
        quests = self.get_active_quests()
        quest_data['id'] = len(quests) + 1
        quest_data['created_at'] = datetime.utcnow().isoformat()
        quests.append(quest_data)
        self.active_quests = json.dumps(quests)
    
    def complete_quest(self, quest_id):
        """Move uma missão para completadas"""
        active_quests = self.get_active_quests()
        completed_quests = json.loads(self.completed_quests) if self.completed_quests else []
        
        for i, quest in enumerate(active_quests):
            if quest.get('id') == quest_id:
                quest['completed_at'] = datetime.utcnow().isoformat()
                completed_quests.append(quest)
                active_quests.pop(i)
                break
        
        self.active_quests = json.dumps(active_quests)
        self.completed_quests = json.dumps(completed_quests)
    
    def get_completed_quests(self):
        return json.loads(self.completed_quests) if self.completed_quests else []
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'character_id': self.character_id,
            'session_name': self.session_name,
            'world_setting': self.world_setting,
            'difficulty_level': self.difficulty_level,
            'current_scene': self.current_scene,
            'current_location': self.current_location,
            'story_context': self.story_context,
            'story_log': self.get_story_log(),
            'player_actions': self.get_player_actions(),
            'world_state': self.get_world_state(),
            'active_quests': self.get_active_quests(),
            'completed_quests': self.get_completed_quests(),
            'ai_settings': {
                'personality': self.ai_personality,
                'difficulty': self.ai_difficulty
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_played': self.last_played.isoformat() if self.last_played else None
        }

