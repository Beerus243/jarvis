"""Moteur de personnalité avancé, sans dépendance réseau ni effet système."""
from collections import deque
import json, re
from pathlib import Path
from core.command_understanding import normalize_command
from personality.dialogue import profile

class AdvancedPersonalityEngine:
    def __init__(self, memory_file=None):
        self.context_history=deque(maxlen=5); self.error_streak=0; self.current_seriousness=0.0; self.user_preferences={}
        path=Path(memory_file or Path(__file__).resolve().parent.parent/'data/user.json')
        try: self.user_preferences=json.loads(path.read_text(encoding='utf-8')).get('preferences', {})
        except (OSError, ValueError): pass
        self._last_responses=deque(maxlen=5)

    def suggest_improvement(self, proposal):
        folder = Path(__file__).resolve().parent.parent / 'data' / 'suggestions'
        folder.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        path = folder / ('suggestion_' + datetime.now().strftime('%Y-%m-%d_%Hh%M') + '.txt')
        path.write_text(str(proposal or '').strip() + '\n', encoding='utf-8')
        return path
    def analyze_context(self,user_input,pc_context=None,personal_context=None):
        text=str(user_input or '').casefold(); self.current_seriousness=1.0 if any(x in text for x in ('urgence','crash','grave','dépêche-toi','depeche toi','bug')) else 0.0
        ref=None
        for pattern,value in ((r'valar\s+morghulis','valar'),(r'\bhobbit\b','hobbit'),(r'\bluke\b','luke'),(r'je suis ton pere','force')):
            if re.search(pattern,text): ref=value; break
        if isinstance(pc_context,dict) and pc_context.get('last_action_success') is False: self.error_streak+=1
        elif isinstance(pc_context,dict) and pc_context.get('last_action_success') is True: self.error_streak=0
        result={'seriousness':self.current_seriousness,'error_streak':self.error_streak,'reference':ref,'personal_context':personal_context or {}}
        self.context_history.append(result); return result
    def select_response(self,action_type,params=None,context=None):
        pools={
            'OPEN_APPLICATION':['Bien sûr, Monsieur.','Très bien.','Entendu.','À votre service.'],
            'VOLUME_UP':['J’augmente le volume. Vous voulez que je prépare des boules Quies pour les voisins ?','Le volume est augmenté, Monsieur. Cela vous semble suffisant ?','Très bien, Monsieur.'],
            'SYSTEM_STATUS':['Examinons les indicateurs disponibles.','Je me fie aux mesures du système.','Les mesures permettront de répondre précisément.'],
            'fallback_general':['Je vous écoute, Monsieur.','Compris, Monsieur.','À votre service, Monsieur.']}
        pool=pools.get(action_type,pools['fallback_general']); serious=(context or {}).get('seriousness',self.current_seriousness)>0.8 or self.error_streak>1
        if serious: pool=pool[:1]
        for response in pool:
            if response not in self._last_responses: self._last_responses.append(response); return response
        response=pool[0]; self._last_responses.append(response); return response
    def handle_banter(self, user_input):
        if self.current_seriousness > .8 or not profile()['humor']:
            return None
        text = normalize_command(user_input)
        responses = {
            'tu reflechis trop': 'Je préfère quelques précautions à une brillante erreur.',
            'je sais ce que je fais': 'Très bien. Une vérification reste une excellente compagne de la confiance.',
            'fais moi confiance': 'Volontiers. Et gardons les vérifications utiles.',
            'c est facile pour toi': 'Disons que j’ai un certain avantage pour les tâches répétitives.',
            'ca va marcher': 'Je l’espère. Le test aura le dernier mot.',
            't es pas drole': 'Je note. Revenons à l’essentiel.',
        }
        return responses.get(text)

    def handle_cultural_reference(self, user_input):
        text = normalize_command(user_input)
        if text == 'valar morghulis':
            return 'Valar Dohaeris.'
        if self.current_seriousness > .8 or not profile()['humor']:
            return None
        if text in {'que la force soit avec toi', 'que la force soit avec vous'}:
            return 'Et avec vous.' if profile()['address'] == 'vous' else 'Et avec toi.'
        if text == 'je suis ton pere':
            return 'Une parenté ambitieuse. Restons sur assistant personnel, si vous le voulez bien.'
        return None
