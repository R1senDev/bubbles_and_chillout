from subprocess import run
from platform   import system
from os.path    import expanduser
from getpass    import getuser


_this_system = system()


if _this_system not in ['Windows', 'Linux']:
    raise RuntimeError(f'Platform {_this_system} is not supported.')


def show_popup(title: str, message: str) -> None:
    match _this_system:
        case  'Windows':
            run(['powershell', '-Command', f'Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show(\'{message}\', \'{title}\')'])
        case 'Linux':
            run(['zenity', '--info', f'--title={title}', f'--text={message}'])
        case _: 
            raise RuntimeError() # this should be unreachable :)


def appdata_path(progname: str) -> str:
    match _this_system:
        case  'Windows':
            return f'C:/Users/{getuser()}/AppData/Local/{progname}'
        case 'Linux':
            return expanduser(f'~/.config/{progname}')
        case _: 
            raise RuntimeError() # this should be unreachable :)