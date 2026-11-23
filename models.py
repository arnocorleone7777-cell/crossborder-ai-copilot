from datetime import date, timedelta
from typing import Literal
import re
from pydantic import BaseModel, Field, model_validator

class Filters(BaseModel):
    start: date = date(2026,10,25)
    end: date = date(2026,10,31)
    platform: Literal['all','TikTok_US','Shopify_DTC','Amazon_US'] = 'all'
    sku: Literal['all','SKU-101','SKU-102','SKU-103','SKU-104','SKU-105'] = 'all'

    @model_validator(mode='after')
    def dates(self):
        if self.end<self.start or (self.end-self.start).days>30:
            raise ValueError('请选择不超过 31 天的有效日期范围')
        return self

    def window(self):
        days=(self.end-self.start).days+1
        return {'start':self.start.isoformat(),'end':self.end.isoformat(),
                'baseline_start':(self.start-timedelta(days=days)).isoformat(),
                'baseline_end':(self.start-timedelta(days=1)).isoformat(),'days':days}

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1,max_length=2000)
    filters: Filters = Field(default_factory=Filters)
    creative: bool = True

ENGLISH_TEXT = r'^[^\u3400-\u9fff]+$'
UNVERIFIED_CLAIM = re.compile(r'\b(effortless|easy|easier|smooth|perfect|guaranteed?|instantly)\b|\bevery time\b|\ball hair types\b|\bease of use\b|\btemperature control\b|\badjustable (heat|temperature)\b|\bbattery life\b|\bfast heating\b|damage[- ]free|不伤发|适合[各所有]*种发质|完美|轻松|高效|快速',re.IGNORECASE)

class ScriptShot(BaseModel):
    time: Literal['0–3s','3–8s','8–12s','12–15s']
    visual: str = Field(min_length=1,max_length=350,pattern=r'^[^\n]*[\u3400-\u9fff][^\n]*$',description='Chinese shooting instructions. Must contain Chinese text. Only cordless design is verified; no other performance claims.')
    voiceover: str = Field(min_length=1,max_length=350,pattern=ENGLISH_TEXT,description='English voiceover only, ideally 6 to 12 words for this shot. No Chinese.')
    overlay: str = Field(min_length=1,max_length=120,pattern=ENGLISH_TEXT,description='Short English on-screen caption only. No Chinese.')

class CreativeCopy(BaseModel):
    headline: str = Field(min_length=1,max_length=70,pattern=ENGLISH_TEXT,description='English poster headline only. No Chinese or unverified product claims.')
    subheadline: str = Field(min_length=1,max_length=140,pattern=ENGLISH_TEXT,description='English poster subtitle only. No Chinese.')
    cta: str = Field(min_length=1,max_length=40,pattern=ENGLISH_TEXT,description='English call to action only. No Chinese.')
    shots: list[ScriptShot] = Field(min_length=4,max_length=4)

    @model_validator(mode='after')
    def fifteen_second_timeline(self):
        if [shot.time for shot in self.shots]!=['0–3s','3–8s','8–12s','12–15s']:
            raise ValueError('Use exactly four chronological shots: 0–3s, 3–8s, 8–12s, 12–15s.')
        return self

    @model_validator(mode='after')
    def verified_claims_and_length(self):
        fields=[('headline',self.headline),('subheadline',self.subheadline),('cta',self.cta)]
        for i,shot in enumerate(self.shots): fields.extend([(f'shots[{i}].voiceover',shot.voiceover),(f'shots[{i}].overlay',shot.overlay)])
        # A conservative list of concrete failure cases observed in this fixture;
        # this does not replace human review of broader advertising claims.
        for name,text in fields:
            match=UNVERIFIED_CLAIM.search(text)
            if match:
                raise ValueError(f'Remove unverified claim "{match.group(0)}" in {name}. Only the product name and cordless design are verified. Replace that field with neutral wording, for example: Take a closer look at cordless styling.')
        words=sum(len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",shot.voiceover)) for shot in self.shots)
        if words>45: raise ValueError('Total voiceover must be at most 45 English words for the 15-second draft.')
        return self

class SQLPlan(BaseModel):
    sql: str = Field(min_length=5,max_length=16000)
    title: str = Field(max_length=120)
    chart_type: Literal['line','bar','funnel','table'] = 'table'
    x_key: str = Field(default='',max_length=80)
    y_keys: list[str] = Field(default_factory=list,max_length=4)
