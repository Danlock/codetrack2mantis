import argparse

from res.MantisUploader import MantisUploader
from res.CodetrackConverter import CodetrackConverter

#Daniel Lockhart 01/14/16 Version 2.1 Now with distutils install!

def setUpParameters():
    parser = argparse.ArgumentParser(description="Convert Codetrack XML bug files into Mantis XML issue files. Deletes issue history and duplicates, using last updated node to check for most recent issue. Uploads to MantisBT upon request.Required Dependencies: beautifulsoup4,requests. Daniel Lockhart 01/08/16 Version 2.1")
    parser.add_argument('input',help="Full filename of Codetrack XML file")
    parser.add_argument('-out','--output',help="Filename of Mantis XML file. ie:mantis",default="mantis")
    parser.add_argument('-date',help="Returns issues submitted after given date.",default="")
    parser.add_argument('-project',help="Removes projects other than the one given. Only needed for multi-project Codetracks. (Card Games for example)",default="")
    parser.add_argument('-url',help="URLBASE of mantis webserver, ie:http://letsdomath.com/mantisbt", default="http://letsdomath.com/mantisbt/")
    return parser.parse_args()

def main():
    args = setUpParameters()

    ctXML = args.input
    mantisFilename = "".join([args.output,".xml"])
    url = args.url
    onlyProject = args.project

    if (args.date == ""):
        cutoff = ""
    else:
        cutoff = dateparser.parse(args.date)

    #converts xml and writes result to disk
    CodetrackConverter(ctXML,mantisFilename,url,onlyProject,cutoff)

    ans = raw_input("Upload to Mantis? (Y/N)\n").lower()

    if ans[0] is not 'y':
        quit(1)

    try:
        MantisUploader(mantisFilename,url).uploadToMantis()
    except:
        print "Upload to mantis failed. Either run this script again or upload " + mantisFilename + " manually."
        raise

if __name__ == '__main__':
    main()