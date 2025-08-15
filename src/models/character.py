from src.models.user import db
import json
from datetime import datetime

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    race = db.Column(db.String(50), nullable=False)
    character_class = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    
    # Atributos principais
    strength = db.Column(db.Integer, default=10)
    dexterity = db.Column(db.Integer, default=10)
    constitution = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    wisdom = db.Column(db.Integer, default=10)
    charisma = db.Column(db.Integer, default=10)
    
    # Pontos de vida e mana
    current_hp = db.Column(db.Integer, default=10)
    max_hp = db.Column(db.Integer, default=10)
    current_mp = db.Column(db.Integer, default=10)
    max_mp = db.Column(db.Integer, default=10)
    
    # Vantagens e desvantagens (JSON)
    advantages = db.Column(db.Text, default='[]')
    disadvantages = db.Column(db.Text, default='[]')
    
    # Sistema de inventário expandido
    equipment = db.Column(db.Text, default='{}')  # Equipamentos equipados
    inventory = db.Column(db.Text, default='[]')  # Itens na bolsa
    gold = db.Column(db.Integer, default=100)     # Moedas de ouro
    
    # NPCs conhecidos pelo personagem
    known_npcs = db.Column(db.Text, default='[]')  # Lista de NPCs que o personagem conhece
    
    # Biografia e notas
    background = db.Column(db.Text, default='')
    notes = db.Column(db.Text, default='')
    
    # Localização atual
    current_location = db.Column(db.String(200), default='Vila Inicial')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Character {self.name}>'
    
    def get_advantages(self):
        return json.loads(self.advantages) if self.advantages else []
    
    def set_advantages(self, advantages_list):
        self.advantages = json.dumps(advantages_list)
    
    def get_disadvantages(self):
        return json.loads(self.disadvantages) if self.disadvantages else []
    
    def set_disadvantages(self, disadvantages_list):
        self.disadvantages = json.dumps(disadvantages_list)
    
    def get_equipment(self):
        return json.loads(self.equipment) if self.equipment else {}
    
    def set_equipment(self, equipment_dict):
        self.equipment = json.dumps(equipment_dict)
    
    def get_inventory(self):
        return json.loads(self.inventory) if self.inventory else []
    
    def set_inventory(self, inventory_list):
        self.inventory = json.dumps(inventory_list)
    
    def add_item_to_inventory(self, item):
        """Adiciona um item ao inventário"""
        inventory = self.get_inventory()
        inventory.append({
            'id': len(inventory) + 1,
            'name': item['name'],
            'description': item.get('description', ''),
            'type': item.get('type', 'misc'),
            'quantity': item.get('quantity', 1),
            'value': item.get('value', 0),
            'rarity': item.get('rarity', 'common'),
            'properties': item.get('properties', {}),
            'acquired_at': datetime.utcnow().isoformat()
        })
        self.set_inventory(inventory)
    
    def remove_item_from_inventory(self, item_id, quantity=1):
        """Remove um item do inventário"""
        inventory = self.get_inventory()
        for i, item in enumerate(inventory):
            if item['id'] == item_id:
                if item['quantity'] <= quantity:
                    inventory.pop(i)
                else:
                    inventory[i]['quantity'] -= quantity
                break
        self.set_inventory(inventory)
    
    def get_known_npcs(self):
        return json.loads(self.known_npcs) if self.known_npcs else []
    
    def add_known_npc(self, npc_data):
        """Adiciona um NPC à lista de conhecidos"""
        known_npcs = self.get_known_npcs()
        
        # Verificar se já conhece este NPC
        for npc in known_npcs:
            if npc['id'] == npc_data['id']:
                # Atualizar informações existentes
                npc.update(npc_data)
                self.known_npcs = json.dumps(known_npcs)
                return
        
        # Adicionar novo NPC
        npc_entry = {
            'id': npc_data['id'],
            'name': npc_data['name'],
            'race': npc_data.get('race', ''),
            'occupation': npc_data.get('occupation', ''),
            'location_met': npc_data.get('location_met', self.current_location),
            'relationship': npc_data.get('relationship', 'neutral'),  # friendly, neutral, hostile
            'notes': npc_data.get('notes', ''),
            'last_interaction': datetime.utcnow().isoformat(),
            'met_at': datetime.utcnow().isoformat()
        }
        known_npcs.append(npc_entry)
        self.known_npcs = json.dumps(known_npcs)
    
    def update_npc_relationship(self, npc_id, relationship, notes=None):
        """Atualiza o relacionamento com um NPC"""
        known_npcs = self.get_known_npcs()
        for npc in known_npcs:
            if npc['id'] == npc_id:
                npc['relationship'] = relationship
                npc['last_interaction'] = datetime.utcnow().isoformat()
                if notes:
                    npc['notes'] = notes
                break
        self.known_npcs = json.dumps(known_npcs)
    
    def can_afford(self, cost):
        """Verifica se o personagem pode pagar um valor"""
        return self.gold >= cost
    
    def spend_gold(self, amount):
        """Gasta ouro"""
        if self.can_afford(amount):
            self.gold -= amount
            return True
        return False
    
    def earn_gold(self, amount):
        """Ganha ouro"""
        self.gold += amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'race': self.race,
            'character_class': self.character_class,
            'level': self.level,
            'experience': self.experience,
            'attributes': {
                'strength': self.strength,
                'dexterity': self.dexterity,
                'constitution': self.constitution,
                'intelligence': self.intelligence,
                'wisdom': self.wisdom,
                'charisma': self.charisma
            },
            'health': {
                'current_hp': self.current_hp,
                'max_hp': self.max_hp,
                'current_mp': self.current_mp,
                'max_mp': self.max_mp
            },
            'advantages': self.get_advantages(),
            'disadvantages': self.get_disadvantages(),
            'equipment': self.get_equipment(),
            'inventory': self.get_inventory(),
            'gold': self.gold,
            'known_npcs': self.get_known_npcs(),
            'background': self.background,
            'notes': self.notes,
            'current_location': self.current_location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

