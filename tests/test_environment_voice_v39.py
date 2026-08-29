from voice.voice_pipeline import VoicePipeline

def test_voice_pipeline_forwards_environment_text_to_brain():
    spoken=[]
    pipeline=VoicePipeline(listener=lambda:'prépare mon environnement Node.js', speaker=spoken.append, brain=lambda text:'plan Node')
    result=pipeline.process_once()
    assert result['success'] and result['response']=='plan Node'
    assert spoken == ['plan Node']
