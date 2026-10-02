"""Modal preferences editor. Changes are previewed, persisted only on explicit save."""
import configparser
from copy import deepcopy
from terminal_ui import DEFAULTS
from preferences import write

SECTIONS = {'layout':'Interface','playback':'Reprodução','pages':'Letras','visualizer':'Visualizador','theme':'Tema','colors':'Cores'}
LABELS = dict(view='Modo de exibição',cover='Capa do álbum',controls='Botões de reprodução',alignment='Alinhamento',vertical='Posição vertical',padding='Margem lateral',line_spacing='Espaço entre linhas',lyrics_width='Largura das letras',border='Borda da janela',show_progress='Barra de progresso',show_source='Origem das letras',history_dim='Suavizar linhas anteriores',active_bold='Frase atual em negrito',click_seek='Clique nas palavras (beta)',font_family='Família da fonte (nova janela)',word_highlight='Destaque de palavra (beta)',font_size='Fonte em pontos (nova janela)',show_hints='Dica de ajuda',show_footer='Rodapé',cursor='Cursor de digitação',icons='Ícones',source='Fonte das letras',player='Player MPRIS',fps='Quadros por segundo',idle_fps='Quadros quando pausado',sync_offset='Ajuste de sincronização (s)',type_ahead='Adiantamento da digitação (s)',typing_mode='Modo de digitação',mode='Modo',min_lines='Mínimo de linhas',max_lines='Máximo de linhas',target_seconds='Duração do bloco (s)',pause_seconds='Pausa entre blocos (s)',gap_animation='Animação de intervalos (beta)',style='Formato',width='Quantidade de bandas',width_percent='Largura em porcentagem',bottom_margin='Distância da borda inferior',height='Altura',bar_spacing='Espaço entre barras',bar_width='Largura de cada barra',smoothing_ms='Suavização (ms)',show_label='Descrição do visualizador',only_gaps='Somente nos intervalos',input='Captura de áudio',sensitivity='Sensibilidade',text='Texto',muted='Texto secundário',accent='Destaque',background='Fundo')
CHOICES = {'layout.view':['full','lyrics'],'layout.alignment':['left','center','right'],'layout.vertical':['top','center','bottom'],'layout.word_highlight':['off','bold-beta'],'playback.source':['native','auto','spicy'],'playback.typing_mode':['smooth','words-beta'],'pages.mode':['dynamic','fixed','rolling'],'visualizer.mode':['auto','spectrum','activity','off'],'visualizer.style':['bars','wave','dots'],'visualizer.input':['auto','pipewire','pulse'],'theme.mode':['static','dynamic']}
DISPLAY = {'true':'Ativado','false':'Desativado','full':'Completo','lyrics':'Somente letras','left':'Esquerda','center':'Centro','right':'Direita','top':'Superior','bottom':'Inferior','off':'Desativado','on':'Ativado','native':'Nativo','auto':'Automático','spicy':'Spicy Lyrics','smooth':'Contínua','words-beta':'Palavras (beta)','bold-beta':'Negrito (beta)','dynamic':'Dinâmico','static':'Fixo','fixed':'Fixo','rolling':'Rolagem','spectrum':'Áudio (CAVA)','activity':'Animação','bars':'Barras','wave':'Onda','dots':'Pontos','default':'Padrão do terminal'}

class SettingsMenu:
    def __init__(self):
        self.open=False
        self.section=0
        self.index=0
        self.hits={}
        self.editing=False
        self.buffer=''
        self.message=''

    def begin(self, values):
        self.original=deepcopy(values)
        self.draft=deepcopy(values)
        self.open=True
        self.editing=False
        self.message=''
        self.revision=0
        self.checked_revision=None

    def key(self):
        section=list(SECTIONS)[self.section]
        keys=list(self.draft[section])
        self.index=min(self.index,len(keys)-1)
        return section,keys[self.index]

    def rows(self):
        section=list(SECTIONS)[self.section]
        return [(LABELS.get(key,key.replace('_',' ').capitalize()),DISPLAY.get(value,value)) for key,value in self.draft[section].items()]

    def step(self, direction):
        section,key=self.key();value=self.draft[section][key]
        choices=CHOICES.get(section+'.'+key)
        if DEFAULTS[section][key] in ('true','false'):
            value='false' if value.lower() in ('true','yes','on','1') else 'true'
        elif choices:
            value=choices[(choices.index(value)+direction)%len(choices)]
        else:
            try:
                float(DEFAULTS[section][key])
                increment=.05 if key in ('sync_offset','type_ahead') else 1
                value=f'{float(value)+direction*increment:.2f}' if increment<1 else str(int(float(value))+direction)
            except ValueError:
                self.editing=True;self.buffer=value
                return
        self.draft[section][key]=value
        self.revision+=1

    def handle(self, event, path):
        kind,value=event
        self.message=''
        if kind=='click':
            action=self.hits.get(value)
            if not action:return None
            if action[0]=='cancel':return self.cancel()
            if self.editing:return None
            if action[0]=='row':
                if self.editing:return None
                self.index=action[1];self.step(1)
                return None
            value=action[0];kind='key'
        if kind=='nav':
            if self.editing:
                if value=='escape':self.editing=False
                return None
            if value in ('up','down'):
                count=len(self.rows());self.index=(self.index+(1 if value=='down' else -1))%count
            elif value in ('left','right'):self.step(1 if value=='right' else -1)
            elif value=='escape':return self.cancel()
            return None
        if kind!='key':return None
        if self.editing:
            if value=='\x1b':self.editing=False
            elif value in ('\r','\n'):
                section,key=self.key();self.draft[section][key]=self.buffer;self.editing=False;self.revision+=1
            elif value in ('\x7f','\b'):self.buffer=self.buffer[:-1]
            elif value.isprintable() and len(self.buffer)<120:self.buffer+=value
            return None
        if value in ('\x1b','q','m','cancel'):return self.cancel()
        if value in ('\t',']','next'):
            self.section=(self.section+1)%len(SECTIONS);self.index=0
        elif value in ('[','previous'):
            self.section=(self.section-1)%len(SECTIONS);self.index=0
        elif value in ('j','k'):
            self.index=(self.index+(1 if value=='j' else -1))%len(self.rows())
        elif value in ('+','-',' ','\r','\n'):self.step(-1 if value=='-' else 1)
        elif value=='e':
            section,key=self.key();self.buffer=self.draft[section][key];self.editing=True
        elif value=='r':
            self.draft=deepcopy(DEFAULTS);self.index=0;self.revision+=1
            self.message='Padrões carregados. Salve para confirmar.'
        elif value in ('s','save'):
            parser=configparser.ConfigParser(interpolation=None);parser.read_dict(self.draft)
            try:write(parser,path)
            except (OSError,ValueError) as error:self.message=str(error);return None
            self.open=False
            return 'saved'
        return None

    def cancel(self):
        self.open=False
        return 'cancelled'

    def preview(self):
        if getattr(self,'checked_revision',None)==self.revision:return self.checked
        import tempfile
        from pathlib import Path
        from terminal_ui import Settings
        parser=configparser.ConfigParser(interpolation=None);parser.read_dict(self.draft)
        with tempfile.TemporaryDirectory(prefix='sylrics-preview-') as folder:
            path=Path(folder)/'ui.ini'
            with path.open('w',encoding='utf-8') as stream:parser.write(stream)
            settings=Settings(path);settings.reload()
            self.checked=None if settings.error else deepcopy(settings.values)
        self.checked_revision=self.revision
        if self.checked is None:self.message='Valor inválido. Ajuste antes de salvar.'
        return self.checked

    @property
    def title(self):return SECTIONS[list(SECTIONS)[self.section]]
