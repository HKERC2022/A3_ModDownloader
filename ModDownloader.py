import cmd
import argparse
import subprocess
import tempfile
import re
from pathlib import Path
class DownloadConsole(cmd.Cmd):
    
    intro = "Welcome to the mod downloader! Type help or ? to list commands.\nPlease Login first"
    
    def __init__(self, appid, args):
        super().__init__()
        self.appid = appid
        self.modlist_name = Path(args.file).name
        self.modlist = self.retrive_modid()
        self.directory = args.dir
        self.steamcmd_path = args.path
    @property
    def prompt(self):
        return f'({self.modlist_name}) '

    def do_download(self,arg):
        """Download mods. Usage: download {id}"""
        try:
            if arg.lower() == "all":
                result = self.download([items[1] for items in self.modlist])
            else:
                result = self.download([self.modlist[int(arg)][1]])
            #cleanup after download
            
            # Fix Later!!!! 
            print("Cleaning up files")
            base = self.directory / Path("steamapps/workshop/content/107410")
            for mod in base.iterdir():
                target = base.parents[3] / ("@"+find_mod_name(self.modlist,mod.name))
                if target.exists():
                    delete_folder_recursive(target)
                mod.rename(target)
            for folder in base.parents[:3]:
                delete_folder_recursive(folder) 
     
        except AttributeError:
            print("Login First!!!. Type: login {username}")
        except ValueError:
            print("You must give a download id")
        except IndexError:
            print(f"Index {arg} out of range, provide a valid id")

           
                    

    def do_list(self, arg):
        """List all the mod"""
        for i, mod in enumerate(self.modlist):
            print(f"{i}: {mod[0]}")
        print("all: download all mods")
        print("\nType: Download {number}\n")
    
    def do_login(self, arg):
        """Login to steamcmd. Usage: login {username}"""
        if (subprocess.call([self.steamcmd_path,"+login", arg, "+quit"]) == 0):
            print("login successful")
            self.username = arg
        else:
            print("login failed. Try again")
    
    def do_exit(self, arg):
        """Exit the shell"""
        print("Bye")
        return True
    
    def do_change_directory(self,arg):
        """Change your donwload directory"""
        if Path(arg).is_dir():
            self.directory = Path(arg)
            print(f"Download directory change to {arg}")
        else:
            print(f"{arg} is not a valid location")

    def do_change_modlist(self,arg):
        """Change mod list"""
        p = Path(arg)
        if (p.suffix.lower() != ".html") or (not p.is_file()):
            print("Mod list location or name is invalid.")
        else:
            print(f"Success change to {arg}")
            self.modlist_name = p.name
            self.modlist = self.retrive_modid()

    def retrive_modid(self):
        with open(self.modlist_name,"r") as file:
            content = file.read()
            div_cut_start = '<div class="mod-list">'
            div_cut_end = '</div>'
            mod_name_start = '<td data-type="DisplayName">'
            mod_name_end = '</td>'
            workshop_id_start = '?id='
            workshop_id_end = '</a>'
            modlist_start_line = content.find(div_cut_start)
            modlistcontent = content[modlist_start_line:content.find(div_cut_end,modlist_start_line)+len(div_cut_end)]
            modlist_list = [] 
            while (modlistcontent.find(mod_name_start) >= 0):
                mod_name_start_index = modlistcontent.find(mod_name_start)
                single_mod = (mod_name_start_index,modlistcontent.find(mod_name_end,mod_name_start_index))
                mod_name = sanitize_filename(modlistcontent[single_mod[0]+len(mod_name_start):single_mod[1]])
                mod_id_end = modlistcontent.find(workshop_id_end)
                mod_id = modlistcontent[modlistcontent.find(workshop_id_start,modlistcontent.find("Link"))+len(workshop_id_start):mod_id_end]

                modlist_list.append([mod_name,mod_id])
                modlistcontent = modlistcontent[mod_id_end+len(mod_name_end):]
            return (modlist_list)

    def download(self, download_items):
        commands = [f"force_install_dir {str(self.directory)}",f"login {self.username}"]
        for item in download_items:
            commands.append(f"workshop_download_item {self.appid} {item}")
        commands.append("quit")
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as temp_script:
            script_path = temp_script.name
            temp_script.write('\n'.join(commands))
        result = subprocess.call([self.steamcmd_path, "+runscript", script_path])
        Path(script_path).unlink()
        return result

def check_steamcmd_file(p):
    path = Path(p)
    if path.name.lower() != "steamcmd.exe":
        raise argparse.ArgumentTypeError(f"The path must point to 'steamcmd.exe': {p}")
    return path.expanduser().resolve()

def check_existing_folder(p):
    path = Path(p)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Not a valid directory: {p}")
    return path.expanduser().resolve()

def check_html_file(p):
    path = Path(p)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Not a file: {p}")
    if path.suffix.lower() != ".html":
        raise argparse.ArgumentTypeError(f"File must be an .html file: {p}")
    return path.expanduser().resolve()


def delete_folder_recursive(path: Path):
    if not path.exists():
        return
    for child in path.iterdir():
        if child.is_dir():
            delete_folder_recursive(child)
        else:
            child.unlink()
    path.rmdir()

def find_mod_name(modlist, modid):
    for mod in modlist:
        if modid == mod[1]:
            return mod[0]

def sanitize_filename(filename):
    # Characters prohibited in Windows filenames
    prohibited_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(prohibited_chars, '-', filename)
    return sanitized

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install mod from steamworkshop")
    parser.add_argument("file", type=check_html_file, help="path to modlist")
    parser.add_argument("-p", "--path", help="path to steamcmd.exe",type=check_steamcmd_file,default="steamcmd.exe")
    parser.add_argument("-d", "--dir", help="Download location",type=check_existing_folder,default=Path.cwd())
    args = parser.parse_args()
    appid = "107410"
    DownloadConsole(appid,args).cmdloop()
         
