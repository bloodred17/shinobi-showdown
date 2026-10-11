"""Explicit scripted stage responses; never loaded by production entrypoints."""
import json
from langchain_core.messages import AIMessage
from helpers import output


def plan_for(proposal, settings, source_turn, source_quote):
    checks = [c['id'] for c in settings['checks']]
    requirements = [{'id': 'R'+str(i), 'statement': criterion, 'origin': 'inference',
                     'source_turn': source_turn, 'source_quote': source_quote}
                    for i, criterion in enumerate(proposal['acceptance_criteria'])]
    scenarios = [{'id':'S'+str(i), 'requirement_ids':[r['id']], 'criterion':i,
                  'given':'The committed fixture baseline', 'action':'Exercise the public behavior',
                  'expected':r['statement'], 'surface':'Public fixture API', 'check_ids':next((a['check_ids'] for a in (settings.get('engineering') or {}).get('acceptance',[]) if a['criterion']==i),checks)}
                 for i,r in enumerate(requirements)]
    return {'requirements':{'revision':1,'requirements':requirements},'scenarios':scenarios,
            'assignments':[{'item_id':i['id'],'requirement_ids':[r['id'] for r in requirements],
                            'scenario_ids':[s['id'] for s in scenarios]} for i in settings['work_items']],
            'selection_reason':'Explicit fixture scenarios with independently protected assertions'}


def stage_generate(messages):
    prompt = '\n'.join(str(m.content) for m in messages if m.type == 'system')
    if 'independent requirements reviewer' not in prompt and 'read-only bug diagnostician' not in prompt:
        return None
    payload,_ = json.JSONDecoder().raw_decode(prompt[prompt.index('{"contract":'):])
    if 'read-only bug diagnostician' in prompt:
        checks=payload['checks']
        data={'symptom':'The public fixture result violates its expected bound',
              'check_ids':[c['id'] for c in checks],
              'hypotheses':['If the source bound is stale, the public high-input assertion fails'],
              'observations':['Recorded controller checks and source identify the fixture bound'],
              'supported_cause':'The fixture implementation uses the previous bound',
              'verdict':'already_satisfied' if all(c['outcome']=='passed' for c in checks) else 'supported'}
        name='Diagnosis'
    else:
        data={'verdict':'pass','summary':'Scripted fixture stage review', 'findings':[],
              'coverage':[{'requirement_id':r['id'],'explanation':'Fixture stage evidence supports the declared scenario'}
                          for r in payload['contract']['lifecycle']['requirements']['requirements']]}
        name='StageReview'
    return output(AIMessage(content='',tool_calls=[{'name':name,'args':data,'id':'stage-result'}]))
