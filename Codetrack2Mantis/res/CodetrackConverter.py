import xml.etree.ElementTree as ET
import res.dateutil.parser as dateparser
import datetime as dt

class CodetrackConverter:

    #keys correspond to mantis, values correspond to codetrack 
    status = {"new":("Open","10"), "closed":("Closed","90"),"acknowledged":("Deferred","30")}

    resolution = {"open" :("Analyzing","Not Fixed","See Comment","Needs Testing","Needs Response","10"), "no change required":("As Designed","70"), 
    "unable to reproduce":("Cannot Recreate","40"), "duplicate":("Duplicate Bug","60"), "suspended":("Change Request","80"),
    "fixed":("Fixed","Fix Released","Enhancement","20")}

    severity = {"minor":("Minor","50"),"tweak":("Cosmetic","40"),"major":("Priority","60"), "feature":("Change Req.","10"), "trivial":("Draft","20"), "crash":("Fatal","70"),
    "block":("Serious","80")}

    conversionTagTable = {"id":"ID","project":"Project","date_submitted":"Submit_Time", "category":"Module","severity":"Severity",
     "summary":"Summary","description":"Description","reporter_username":"Submitted_By", "additional_information":"Developer_Comment",
     "resolution":"Developer_Response","handler_username":"Assign_To", "status":"Status", "version":"Version", "date":"Last_Updated"}

    def __init__(self,ctXML,mantisFilename,url,onlyProject,cutoff):
        print "Converting " + ctXML + "..."
        self.issue_IDS = []
        self.duplicates = []

        xml = ET.parse(ctXML)
        root = xml.getroot()
        root.tag = "mantis"

        root.set("urlbase",url)
        root.set("issuelink","#")
        root.set("notelink","~")
        root.set("format","1")


        for child in root:
            self.convertBugtoIssue(child)
        #Codetrack outputs stupid XML
        self.deleteDuplicateIssues(root)
        #if date provided delete previous issues
        self.removeIssuesBefore(cutoff,root)
        #multiproject codetrack compatibility working
        self.removeIssuesExcept(onlyProject,root)

        for c in root:
            self.convertDates(c)

        xml.write(mantisFilename,encoding="utf-8",xml_declaration=True)
        print "Issues have been converted and placed into " + mantisFilename + "."

        
    #Converts dates to a datetime obj and finds the youngest
    def mostRecent(self,args):
        if isinstance(args, basestring):
            return dateparser.parse(args)
        else:
            dates = []
            for d in args:
                dates.append(dateparser.parse(d))
            return max(dates)

    def convertValueToKey(self,table,node):
        for key,value in table.iteritems() :
            if (any(node.text in v for v in value[:-1])):
                node.text = key
                node.set("id",value[-1])

    #translates unknown fields to mantis equivalents
    def translate(self,version,node):
        if (version == "status"):
            self.convertValueToKey(self.status,node)
        elif(version == "severity"):
            self.convertValueToKey(self.severity,node)
        elif (version == "resolution"):
            self.convertValueToKey(self.resolution,node)
        else:
            return

    def contains(self,txt):
        for i in self.issue_IDS:
            if i[0] == txt:
                return i[1]
        return None

    #Codetrack lists issues several times, delete all but the latest version of issue
    def deleteDuplicateIssues(self,root):
        self.duplicates.sort()
        done = []
        for i in self.duplicates:
            if not i[0] in done:
                current = [c for c in self.duplicates if c[0] == i[0]]
                dates = []
                nodes = []
                for z,node in current:
                     d = node.find("date")
                     dates.append(d.text)
                     nodes.append(((d.text),node))
                recent = self.mostRecent(dates)
                done.append(i[0])
                for x in nodes:
                    if recent != self.mostRecent(x[0]):
                        root.remove(x[1])
        return

    def convertBugtoIssue(self,bug):
        bug.tag = "issue"
        pid = ET.SubElement(bug,'profile_id')
        pid.text = "1"
        attr = {'id':"10"}
        proj = ET.SubElement(bug,'projection',attr)
        proj.text = "none"
        eta = ET.SubElement(bug,'eta',attr)
        eta = "none"
        view = ET.SubElement(bug,'view_state',attr)
        view.text = "public"
        due = ET.SubElement(bug,'due_date')
        due.text = "1"

        for node in bug:
            for k,v in self.conversionTagTable.iteritems():
                if node.tag == v:
                    node.tag = k
            if node.tag == "id":
                bugID = node.text
                if any(node.text in i[0] for i in self.issue_IDS):
                    if any(node.text in i[0] for i in self.duplicates):
                        self.duplicates.append((node.text,bug))
                    else:
                        self.duplicates.append((node.text,bug))
                        #Only find out duplicate once we on the 2nd bug. Must get back to the first bug
                        self.duplicates.append((node.text,self.contains(node.text)))
                elif self.contains(node.text) == None:
                    self.issue_IDS.append((node.text,bug))
            elif node.tag == "reporter_username":
                reporter = node.text
            self.translate(node.tag,node)
        date = bug.find("date").text
        bug.find("summary").text += " (" + reporter + " on " + date + ", Codetrack #" + bugID + ")"

    def removeIssuesBefore(self,date,root):
        if date == "":
            return
        deletion = []
        for node in root:
            issue_date = node.findtext("date")
            if dateparser.parse(issue_date) < date:
                deletion.append(node)

        for d in deletion:
            root.remove(d)

    def removeIssuesExcept(self,category,root):
        if category == "":
            return
        deletion = []
        for node in root:
            node_cat = node.findtext("project")
            if node_cat != category:
                deletion.append(node)

        for d in deletion:
            root.remove(d)

    #Correctly converts dates, but mantis overrides date with time issues are submitted into mantis. 
    def convertDates(self,bug):
        for node in bug:
            if node.tag == 'date':
                date = node
            elif node.tag == 'date_submitted':
                dateSub = node

        date_obj = dateparser.parse(date.text)
        dateSub_obj = dateparser.parse(dateSub.text)

        epoch = dt.datetime.utcfromtimestamp(0)
        #round datetime and convert it to proper format for mantis xml, which is Epoch time
        date.text = str(int((date_obj - epoch).total_seconds()))
        dateSub.text = str(int((dateSub_obj - epoch).total_seconds()))