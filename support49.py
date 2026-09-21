"""User-requested diagnostics. Reports omit usernames, paths and raw crash logs."""
import json,platform
from pathlib import Path
import pygame
from release_info import VERSION

def snapshot(app):
    return {'game_version':VERSION,'python':platform.python_version(),'os':platform.system(),
            'os_release':platform.release(),'pygame':pygame.version.ver,'sdl':list(pygame.get_sdl_version()),
            'display_driver':pygame.display.get_driver(),'window_size':list(app.window.get_size()),
            'audio_available':bool(app.audio.available),'controller_support':bool(app.controls.enabled),
            'connected_controllers':len(app.controls.pads),'input_recovered':bool(getattr(app,'input_recovered',False)),
            'save_integrity':app.store.db.execute('PRAGMA quick_check').fetchone()[0],
            'backup_issue':bool(app.store.backup_error)}

def export(app):
    folder=app.store.directory/'exports';folder.mkdir(exist_ok=True)
    path=folder/'support_report.json';path.write_text(json.dumps(snapshot(app),indent=2),encoding='utf-8')
    return path

def check_setup():
    import tempfile
    from main import App
    from journey47 import map_report
    from model import default_save_dir
    report={'game_version':VERSION,'checks':[]};app=None
    try:
        with tempfile.TemporaryDirectory() as directory:
            try:
                app=App(directory)
                app.events()
                report['system']=snapshot(app)
                report['checks'].append({'name':'Window and input queue','passed':not getattr(app,'input_recovered',False)})
                for tier in range(5):
                    app.start(tier);app.draw();r=map_report(app.game)
                    report['checks'].append({'name':f'Biome {tier+1} generation and render','passed':r['reachable'] and r['spawn_distance']>=16})
            finally:
                if app:app.close()
    except Exception as exc:
        report['checks'].append({'name':'Setup check','passed':False,'error_type':type(exc).__name__})
    report['passed']=all(c['passed'] for c in report['checks'])
    folder=default_save_dir()/'exports';folder.mkdir(parents=True,exist_ok=True)
    path=folder/'setup_check.json';path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('SETUP CHECK '+('PASSED' if report['passed'] else 'NEEDS ATTENTION'))
    print('Report saved to:',path)
    print('This checks startup and rendering only. Actual controller input and long play sessions still need testing.')
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(check_setup())
