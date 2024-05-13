class Label:
    def __init__(self, id: str, text: str, rationale: str, decision:str, is_gpt:bool) -> None:
        self.id = id
        self.text = text
        self.rationale = rationale
        self.is_validated = False
        self.is_selected = False
        self.decision = decision
        self.is_gpt = is_gpt
        self.definition = None
        self.rejection = None

class Example:
    def __init__(self, id:str, original:str, revised:str, context:str, label_id:str, decision:str, is_gpt:bool) -> None:
        self.id = id 
        self.original = original
        self.revised = revised 
        self.context = context
        self.label_id = label_id 
        self.is_validated = False
        self.is_selected = False
        self.decision = decision
        self.is_gpt = is_gpt
        self.rejection = None
