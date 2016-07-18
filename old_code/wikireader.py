#!/usr/bin/python

def readVersion(file, title):
    """
    """
    content = open(file, "r")
    wikicontent = open(title+".html", "w")
    wikicontent.write("<!DOCTYPE html>\n<html>\n<head>\n")
    wikicontent.write('<link rel="stylesheet" type="text/css" href="wikistyle.css">')
    wikicontent.write("<style/>\n")
    wikicontent.write(".link {\n\tcolor: blue;\n}\n")


   
    

    wikicontent.write("</style>")
    wikicontent.write("<body>\n")

    for line in content:
        if line[0] == "=":
            count = 0
            for i in range(len(line)):
                if line[i] == "=":
                    count+=1
                else:
                    break
            heading = "h"+str(count)
            wikicontent.write("<"+heading+">"+line.strip("=")+"</"+heading+">\n")

        else:
            current = ""
            end = False
            count = 0
            brackets = 0
            for i in range(len(line)):
                if line[i] == "'":
                    count += 1
                elif line[i]=="[":
                    if brackets==0:
                        brackets+=1
                    else:
                        brackets=0
                        current+="<span class= link>"
                elif line[i] == "]":
                    if brackets==0:
                        brackets+=1
                    else:
                        brackets=0
                        current+="</span>"


                elif end:
                    if count == 3:
                        current+= '</b>' + line[i]
                        count = 0
                        end = False
                    elif count == 2:
                        current+= '</i>' + line[i]
                        count = 0
                        end = False
                    elif count == 5:
                        current+= '</i></b>' + line[i]
                        count = 0
                        end = False
                    else:
                        current+= line[i]
                else:
                    if count == 3:
                        current+= '<b>' + line[i]
                        count = 0
                        end = True
                    elif count == 2:
                        current+= '<i>' + line[i]
                        count = 0
                        end = True
                    elif count == 5:
                        current+= '<b><i>' + line[i]
                        count = 0
                        end = True
                    else:
                        current+= line[i]
                
            if end:
                if count == 3:
                    current+= '</b>'
                elif count == 2:
                    current+= '</i>'
                elif count == 5:
                    current+= '</i></b>'
                    
        
            
            wikicontent.write("<p>" + current + "\n</p>")
    wikicontent.write("</body>\n</html>")
    wikicontent.close()
    content.close()
        

readVersion('content/Mesostigma.txt', "Meso")