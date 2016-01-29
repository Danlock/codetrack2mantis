from bs4 import BeautifulSoup
import getpass
import requests

class MantisUploader:

    def __init__(self,fname,base_url):
        #tried to make it a bit more portable by using base_url but will need to parse base_url for mantisbt section to truly make portable, currently needs mantis to be in of "www.foo.bar/mantisbt" 
        self.UPLOAD_URL = base_url + "plugin.php?page=XmlImportExport/import_action"
        self.SELECT_PROJECT_URL = base_url + "login_select_proj_page.php"
        self.SELECT_PROJECT_FORM_URL = base_url + "set_project.php?ref=/mantisbt/plugin.php?page=XmlImportExport%2Fimport"
        self.LOGIN_URL = base_url + "login.php"
        self.LOGOUT_URL = base_url + "logout_page.php"
        self.filename = fname

    def askForLogin(self):
        user = raw_input("Mantis username: ")
        pw = getpass.getpass("Mantis password: ")
        
        return {'username':user,'password':pw}


    def uploadToMantis(self):
        login = self.askForLogin()
        login["secure_session"] = 1

        project = {
        'project_id' : '24',
        'ref' : r'/mantisbt/plugin.php?page=XmlImportExport%2Fimport'
        }

        uploadData = {
        'project_id' : '24',
        'max_file_size' : '5000000',
        'step' : '1',
        'strategy' : 'link',
        'fallback' : 'disable',
        'defaultcategory' : '1',
        'plugin_xml_import_action_token' : ''
        }

        project_list = {}

        with requests.Session() as s:
            try:
                #logout for clean state
                s.get(self.LOGOUT_URL)
                #login
                success = 1
                while(success != 0):
                    r1 = s.post(self.LOGIN_URL, data=login)
                    soup = BeautifulSoup(r1.text,"html.parser")
                    loginCheck = soup.find_all(string="Your account may be disabled or blocked or the username/password you entered is incorrect.")
                    success = len(loginCheck)
                    if success is 0:
                        print 'Login Successful.'
                    else:
                        ans = raw_input('Login Unsuccessful. Try again? (Y/N)\n').lower()
                        if (ans[0] == 'n'):
                            quit(1)
                        else:
                            relogin = self.askForLogin()
                            login["username"] = relogin["username"]
                            login["password"] = relogin["password"]

                #select project
                r2 = s.get(self.SELECT_PROJECT_URL,data=project)
                project_list =  self.parseProjects(r2.text)
                uploadData["project_id"] = project["project_id"] = self.getProjectFromUser(project_list)

                r3 = s.post(self.SELECT_PROJECT_FORM_URL,params=project)
                self.logoutOnException(s,r3,self.LOGOUT_URL)

                #Parse for form security token
                soup = BeautifulSoup(r3.text,'html.parser')
                l = soup.find(attrs={"name":"plugin_xml_import_action_token"})
                tkn = l.get('value')
                uploadData["plugin_xml_import_action_token"] = tkn

                r4 = s.post(self.UPLOAD_URL,data=uploadData,files={'file' : open(self.filename, 'rb')})
                self.logoutOnException(s,r4,self.LOGOUT_URL)

                soup = BeautifulSoup(r4.text,'html.parser')
                
                print "Upload to " + project_list[project["project_id"]] + " was successful.\nMantis response:\n\t##\t##\t##"
                for text in soup.find_all("pre"):
                    print text.getText()
                print "\t##\t##\t##"
            finally:
                #logout when finished
                r5 = s.get(self.LOGOUT_URL)

    def getProjectFromUser(self,plist):
        print "Printing list of available projects and their ids.\n"

        for i,p in sorted(plist.items()):
            if i == "0":
                continue
            print i + "\t" + p

        ans = "0"
        while (ans == "0"):
            ans = raw_input('\nEnter the destination project\'s id.\n')
            if ans not in plist.keys():
                ans = "0"
                print "Incorrect ID. Please enter project id."
        return ans


    def parseProjects(self,html):
        soup = BeautifulSoup(html,'html.parser')
        l = soup.find(attrs={"name":"project_id"})
        project_list = {}
        for opt in l.find_all('option'):
            key = opt.getText().encode('ascii','ignore')
            key = key.replace("\xa0\xbb ","").strip()
            project_list[opt.get("value")] = key
        return project_list

    def logoutOnException(self,sesh,req,logout):
        try:
            req.raise_for_status
        except:
            sesh.get(logout)
            raise       