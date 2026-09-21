"""Consistent SQLite backups and an explicit, non-destructive recovery command."""
from pathlib import Path
import os
import shutil
import sqlite3
import time


def backup_store(store):
    folder=store.directory/'backups'; folder.mkdir(exist_ok=True)
    temporary=folder/'pending.sqlite3'
    try:
        with sqlite3.connect(temporary) as dest:
            store.db.backup(dest)
            if dest.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                raise sqlite3.DatabaseError('Backup integrity check failed')
        for n in (2,1):
            source=folder/f'progress-{n}.sqlite3'
            if source.exists(): os.replace(source,folder/f'progress-{n+1}.sqlite3')
        os.replace(temporary,folder/'progress-1.sqlite3')
    finally:
        if temporary.exists(): temporary.unlink()


def restore_backup(directory,index=1):
    directory=Path(directory); source=directory/'backups'/f'progress-{index}.sqlite3'
    if index not in (1,2,3) or not source.is_file(): raise ValueError('That backup is not available.')
    with sqlite3.connect(f'{source.as_uri()}?mode=ro',uri=True) as db:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok': raise ValueError('Backup is damaged.')
        if not {'settings','mazes','runs'} <= {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
            raise ValueError('This is not an Applin Escape save.')
    preserved=directory/('before-recovery-'+str(time.time_ns())); preserved.mkdir()
    for name in ('progress.sqlite3','progress.sqlite3-wal','progress.sqlite3-shm'):
        p=directory/name
        if p.exists(): shutil.copy2(p,preserved/name)
    temporary=directory/'restore-pending.sqlite3'; shutil.copy2(source,temporary)
    os.replace(temporary,directory/'progress.sqlite3')
    for suffix in ('-wal','-shm'):
        p=directory/('progress.sqlite3'+suffix)
        if p.exists(): p.unlink()
    return preserved


if __name__=='__main__':
    from model import default_save_dir
    directory=default_save_dir()
    print('Close Applin Escape before recovery. Your current save will be preserved.')
    for index in (1,2,3):
        p=directory/'backups'/f'progress-{index}.sqlite3'
        if p.exists(): print(f'{index}: {time.ctime(p.stat().st_mtime)}')
    choice=input('Backup number to restore (Enter cancels): ').strip()
    if choice:
        try: print('Save restored. Previous files preserved at:',restore_backup(directory,int(choice)))
        except (ValueError,OSError,sqlite3.Error) as exc: print('Recovery could not complete:',exc)
