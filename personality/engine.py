"""Moteur de personnalité avancé, sans dépendance réseau ni effet système."""
from collections import deque
import json, re
from pathlib import Path

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
            'OPEN_APPLICATION':['Bien sûr, Monsieur.','Je m’en occupe. Le thé sera prêt dans cinq minutes.','Comme vous voulez. J’ai vérifié qu’elle était à jour.','La voici, Monsieur. Essayez de ne pas la planter, j’ai déjà assez de travail.'],
            'VOLUME_UP':['J’augmente le volume. Vous voulez que je prépare des boules Quies pour les voisins ?','Le volume est augmenté, Monsieur. Cela vous semble suffisant ?','Très bien, Monsieur.'],
            'SYSTEM_STATUS':['Tout fonctionne dans les limites acceptables. Pour l’instant.','Le système est stable. Je n’ose pas dire « pour l’instant » de peur de le tenter.','Les indicateurs sont convenables, Monsieur.'],
            'fallback_general':['Je vous écoute, Monsieur.','Compris, Monsieur.','À votre service, Monsieur.']}
        pool=pools.get(action_type,pools['fallback_general']); serious=(context or {}).get('seriousness',self.current_seriousness)>0.8 or self.error_streak>1
        if serious: pool=pool[:1]
        for response in pool:
            if response not in self._last_responses: self._last_responses.append(response); return response
        response=pool[0]; self._last_responses.append(response); return response
    def handle_banter(self,user_input):
        if self.current_seriousness>0.8: return None
        text=str(user_input or '').casefold()
        if 'tu reflechis trop' in text or 'tu réfléchis trop' in text: return 'Avec tout le respect que je vous dois, c’est précisément pour cela que je suis là.'
        if 'je sais ce que je fais' in text or 'fais moi confiance' in text: return 'Je vous fais confiance. C’est le code qui m’inspire des réserves.'
        if 'c est facile pour toi' in text or "c'est facile pour toi" in text: return 'Je suis une machine, Monsieur. Mais même moi, j’apprécie un peu de considération.'
        if 'ca va marcher' in text or 'ça va marcher' in text: return 'C’est ce que nous disions la dernière fois. Le café est prêt, au cas où.'
        if 't es sur' in text or "t'es sûr" in text: return 'Aussi sûr que possible. Mais je garde une gomme effaçable à portée de main.'
        if 't es pas drole' in text or "t'es pas drôle" in text: return 'Je ne suis pas payé pour être drôle, Monsieur. Je suis payé pour votre sécurité.'
        return None
    def handle_cultural_reference(self,user_input):
        text=str(user_input or '').casefold()
        if re.search(r'valar\s+morghulis',text): return 'Valar Dohaeris.'
        if re.search(r'que la force',text) and self.current_seriousness<=0.8: return 'Et avec vous, Monsieur.'
        if re.search(r'je suis ton pere',text): return 'Cela expliquerait beaucoup de choses. Mais non, je ne suis que le majordome.'
        return None
