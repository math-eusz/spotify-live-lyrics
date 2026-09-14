"""Unified native/automatic/Spicy player for sylrics 0.7.1."""
import os
import select
import shutil
import sys
import termios
import time
import tty
from bridge_runtime import Bridge
from paging import Pages
from sources import Player, Lyrics, Clock
from terminal_ui import TerminalUI, Settings
from visualizer import Visualizer


def same_track(a,b):
    if not a or not b:
        return False
    # The MPRIS and Spicetify URI representations can differ.
    return (a['artist'].casefold(),a['title'].casefold()) == (b['artist'].casefold(),b['title'].casefold()) and (
        not a.get('duration') or not b.get('duration') or abs(a['duration']-b['duration'])<3)


def choose_source(mode,native,spicy,spicy_lines):
    if mode=='native':
        return native, [], 'Nativo'
    if mode=='spicy':
        return spicy, spicy_lines, 'Spicy Lyrics'
    if spicy and (not native or same_track(native,spicy)) and spicy_lines:
        return spicy,spicy_lines,'Spicy Lyrics'
    return native or spicy, [], 'Nativo'


class Keyboard:
    def __enter__(self):
        self.saved=None
        if sys.stdin.isatty():
            self.saved=termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
        return self

    def read(self):
        if self.saved and select.select([sys.stdin],[],[],0)[0]:
            return os.read(sys.stdin.fileno(),32).decode(errors='ignore')
        return ''

    def __exit__(self,*args):
        if self.saved:
            termios.tcsetattr(sys.stdin.fileno(),termios.TCSADRAIN,self.saved)


def run(path,source=None,demo=False):
    from pathlib import Path
    from lrc_store import LrcStore
    LrcStore().maintain(import_from=Path.home())
    if not sys.stdout.isatty() and not demo:
        print('Abra um terminal interativo ou use sylrics doctor.')
        return 1
    settings=Settings(path)
    settings.reload()
    if settings.error:
        print(settings.error)
        return 1
    mode=source or settings.values['playback']['source']
    if not demo and mode=='native' and not shutil.which('playerctl'):
        print('playerctl não encontrado. No Arch/CachyOS: sudo pacman -S playerctl')
        return 1
    ui=TerminalUI(settings)
    loader=Lyrics() if not demo else None
    native=bridge=None
    player_name=None
    pages=Pages()
    clock=Clock()
    visual=Visualizer()
    notice=''
    notice_until=0
    session={}
    signature=settings.signature
    help_open=False
    started=time.monotonic()
    demo_lines=[]
    if demo:
        from lyrics import parse_lyrics
        demo_lines=parse_lyrics('[00:03.00]Uma interface que acompanha a música\n[00:06.00]Cada palavra no seu lugar\n[00:09.00]O ritmo encontra espaço\n[00:12.00]\n[00:18.00]E a próxima frase pode começar\n[00:22.00]Do seu jeito, no seu terminal\n[00:26.00]')
    print('\033[?1049h\033[?25l',end='',flush=True)
    try:
        with Keyboard() as keyboard:
            while True:
                tick=time.monotonic()
                settings.reload()
                if settings.signature != signature:
                    session.clear()
                    signature=settings.signature
                for (section,key),value in session.items():
                    settings.values[section][key]=value
                playback=settings.values['playback']
                mode=source or playback['source']
                if not demo:
                    wanted=playback['player']
                    if (mode!='spicy' or shutil.which('playerctl')) and wanted!=player_name:
                        if native:
                            native.close()
                        native=Player(wanted) if shutil.which('playerctl') else None
                        player_name=wanted
                    if mode!='native' and bridge is None:
                        bridge=Bridge()
                    elif mode=='native' and bridge:
                        bridge.close()
                        bridge=None
                visual.configure(settings.values['visualizer'])
                keys=keyboard.read()
                if 'q' in keys:
                    break
                for key in keys:
                    if key in ' np' and native:
                        native.control({' ':'play-pause','n':'next','p':'previous'}[key])
                    if key=='v':
                        modes=['auto','spectrum','activity','off']
                        value=modes[(modes.index(settings.values['visualizer']['mode'])+1)%len(modes)]
                        session['visualizer','mode']=value
                        notice='Visualizador: '+value
                        notice_until=tick+3
                    if key=='s':
                        session['layout','show_source']='false' if settings.flag('show_source') else 'true'
                    if key=='a':
                        values=['left','center','right']
                        session['layout','alignment']=values[(values.index(settings.values['layout']['alignment'])+1)%3]
                    if key in '+-':
                        value=max(-10,min(10,float(playback['sync_offset'])+(.05 if key=='+' else -.05)))
                        session['playback','sync_offset']=f'{value:.2f}'
                        notice=f'Sincronização: {value:+.2f}s (sessão)'
                        notice_until=tick+3
                    if key=='r':
                        modes=['dynamic','fixed','rolling']
                        value=modes[(modes.index(settings.values['pages']['mode'])+1)%len(modes)]
                        session['pages','mode']=value
                        notice='Leitura: '+value
                        notice_until=tick+3
                    if key=='h':
                        session['layout','word_highlight']='off' if settings.values['layout']['word_highlight']=='bold-beta' else 'bold-beta'
                    if key=='?':
                        help_open=not help_open
                    for (section,option),value in session.items():
                        settings.values[section][option]=value
                if demo:
                    data=dict(uri='demo',artist='sylrics',title='Prévia interativa · 0.7.1',duration=30,
                              position=(tick-started)%30,measured_at=tick,playing=True)
                    lines,label=demo_lines,'Demonstração'
                else:
                    spicy,spicy_lines,_=bridge.snapshot() if bridge else (None,[],None)
                    data,lines,label=choose_source(mode,native.snapshot() if native else None,spicy,spicy_lines)
                    if data and not lines:
                        lines,provider=loader.get(data)
                        label='Nativo · '+provider
                if data:
                    position=clock.position(data,tick)+float(playback['sync_offset'])
                    if lines:
                        body,anchor,gap=pages.render(lines,position,settings.values['pages'],float(playback['type_ahead']),playback['typing_mode'])
                    else:
                        body=anchor=label.split(' · ',1)[-1]
                        gap=True
                    bars=visual.frame(settings.values['visualizer'],data['playing'],gap,tick)
                    ui.draw(data['artist'],data['title'],body,position,data.get('duration',0),data['playing'],
                            label,anchor,visual=bars,gap=gap,help_open=help_open,notice=notice if tick<notice_until else '')
                else:
                    message='Abra um player compatível e toque uma música.' if mode!='spicy' else (
                        bridge.error or 'Abra a letra no Spicy Lyrics para conectar.')
                    ui.draw('','sylrics · 0.7.1',message,playing=False,
                            notice='sylrics doctor · Diagnóstico',source=mode,help_open=help_open)
                time.sleep(max(0,1/int(playback['fps'])-(time.monotonic()-tick)))
    except KeyboardInterrupt:
        pass
    finally:
        if native:
            native.close()
        if loader:
            loader.close()
        visual.close()
        if bridge:
            bridge.close()
        print('\033[0m\033[?25h\033[?1049l',end='',flush=True)
    return 0

