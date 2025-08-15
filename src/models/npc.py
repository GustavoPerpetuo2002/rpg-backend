from src.models.user import db
import json
from datetime import datetime

class NPC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    race = db.Column(db.String(50), nullable=False)
    occupation = db.Column(db.String(100), default='')
    
    # Atributos principais
    strength = db.Column(db.Integer, default=10)
    dexterity = db.Column(db.Integer, default=10)
    constitution = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    wisdom = db.Column(db.Integer, default=10)
    charisma = db.Column(db.Integer, default=10)
    
    # Personalidade e IA
    personality_traits = db.Column(db.Text, default='[]')  # JSON array
    goals_short_term = db.Column(db.Text, default='[]')    # JSON array
    goals_long_term = db.Column(db.Text, default='[]')     # JSON array
    fears = db.Column(db.Text, default='[]')               # JSON array
    relationships = db.Column(db.Text, default='{}')       # JSON object
    
    # Histórico e memórias
    memory_log = db.Column(db.Text, default='[]')          # JSON array de eventos
    interaction_history = db.Column(db.Text, default='[]') # JSON array de interações
    
    # Status atual
    current_location = db.Column(db.String(200), default='')
    current_activity = db.Column(db.String(200), default='')
    mood = db.Column(db.String(50), default='neutral')
    
    # Evolução e aprendizado
    skill_points = db.Column(db.Integer, default=0)
    learned_skills = db.Column(db.Text, default='[]')      # JSON array
    reputation = db.Column(db.Integer, default=0)          # -100 a +100
    
    # Aparência e descrição
    physical_description = db.Column(db.Text, default='')
    clothing_description = db.Column(db.Text, default='')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NPC {self.name}>'
    
    def get_personality_traits(self):
        return json.loads(self.personality_traits) if self.personality_traits else []
    
    def set_personality_traits(self, traits_list):
        self.personality_traits = json.dumps(traits_list)
    
    def get_goals_short_term(self):
        return json.loads(self.goals_short_term) if self.goals_short_term else []
    
    def set_goals_short_term(self, goals_list):
        self.goals_short_term = json.dumps(goals_list)
    
    def get_goals_long_term(self):
        return json.loads(self.goals_long_term) if self.goals_long_term else []
    
    def set_goals_long_term(self, goals_list):
        self.goals_long_term = json.dumps(goals_list)
    
    def get_fears(self):
        return json.loads(self.fears) if self.fears else []
    
    def set_fears(self, fears_list):
        self.fears = json.dumps(fears_list)
    
    def get_relationships(self):
        return json.loads(self.relationships) if self.relationships else {}
    
    def set_relationships(self, relationships_dict):
        self.relationships = json.dumps(relationships_dict)
    
    def get_memory_log(self):
        return json.loads(self.memory_log) if self.memory_log else []
    
    def add_memory(self, memory_entry):
        memories = self.get_memory_log()
        memories.append({
            'timestamp': datetime.utcnow().isoformat(),
            'event': memory_entry
        })
        self.memory_log = json.dumps(memories)
    
    def get_interaction_history(self):
        return json.loads(self.interaction_history) if self.interaction_history else []
    
    def add_interaction(self, interaction_entry):
        interactions = self.get_interaction_history()
        interactions.append({
            'timestamp': datetime.utcnow().isoformat(),
            'interaction': interaction_entry
        })
        self.interaction_history = json.dumps(interactions)
    
    def get_learned_skills(self):
        return json.loads(self.learned_skills) if self.learned_skills else []
    
    def add_skill(self, skill_name):
        skills = self.get_learned_skills()
        if skill_name not in skills:
            skills.append(skill_name)
            self.learned_skills = json.dumps(skills)
    
    def to_dict(self):
        return {
            'id': self.id,
            'game_session_id': self.game_session_id,
            'name': self.name,
            'race': self.race,
            'occupation': self.occupation,
            'attributes': {
                'strength': self.strength,
                'dexterity': self.dexterity,
                'constitution': self.constitution,
                'intelligence': self.intelligence,
                'wisdom': self.wisdom,
                'charisma': self.charisma
            },
            'personality': {
                'traits': self.get_personality_traits(),
                'goals_short_term': self.get_goals_short_term(),
                'goals_long_term': self.get_goals_long_term(),
                'fears': self.get_fears(),
                'relationships': self.get_relationships()
            },
            'status': {
                'current_location': self.current_location,
                'current_activity': self.current_activity,
                'mood': self.mood,
                'reputation': self.reputation
            },
            'appearance': {
                'physical_description': self.physical_description,
                'clothing_description': self.clothing_description
            },
            'memory_log': self.get_memory_log(),
            'interaction_history': self.get_interaction_history(),
            'learned_skills': self.get_learned_skills(),
            'skill_points': self.skill_points,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None
        }

