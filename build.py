from PyInstaller.__main__ import run

if __name__ == '__main__':
    run([
        'lobby.py',
        '--name=MomongaXray',
        '--onefile',
        '--noconsole',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
                '--icon=favicon.png',

        '--hidden-import=PIL._imaging',
        '--hidden-import=PIL._imagingtk',
        '--clean',
        '--uac-admin',
    ])
