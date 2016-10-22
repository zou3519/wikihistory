#!/usr/bin/python

import os
import wiki2graph as w2g

# Assumes the existence of a dictionary from an applied metric,
#   a content file, and a model file


NUMSHADES = 1791
NUMHUE = 180
SATURATION = 100
LIGHTNESS = 50

"""def getHue(model, metricDict):

    a=[(metricDict[x[1]], x[1]) for x in model]
    s=set(a)
    a=sorted(list(s), reverse=True)
    length=len(a)
    x=float(length)/NUMHUE

    colors = {}
    for i in range(length):
        colors[a[i][1]]=col.husl_to_hex(int(float(i)/x), SATURATION, LIGHTNESS)

    return colors"""


def metric2HUSL(title, remove, metricName, metricDict):
    """
        Writes a heatmap of the most recent revision of title as a .html
            file in heatmaps, based on the percentile of the text according
            to metricDict.
    """
    file = title.replace(' ', '_') + ('_rem' if remove else '') + '.txt'
    content = w2g.readContent('content/' + file)
    model = w2g.readModel('GMLs/' + file)
    colors = getHue(model, metricDict)
    writeHues(title, remove, metricName, model, content, colors)


def writeHues(title, remove, metricName, model, content, colors):
    """
        Writes the most recent revision to a .html file based on the shades in the
            dictionary, colors.
        metricName will be part of the file title
    """
    print "Writing heat map . . ."

    if not os.path.isdir('heatmaps'):
        os.mkdir('heatmaps')

    if remove:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + "_rem.html", "w")
    else:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + ".html", "w")

    # Write style sheet
    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style>\n")
    colorFile.write("p {\n\tcolor: black;\n}\n")

    # Write content
    colorFile.write("</style><body>\n")

    content = content.split("\n")
    content = [line.split() for line in content]

    pos = 0
    dif = model[pos][0]
    color = colors[model[pos][1]]

    for line in content:
        current = "<p><span style=background-color:" + color + ";>"
        for i in range(len(line)):
            if dif == 0:
                while dif == 0:
                    pos += 1
                    color = colors[model[pos][1]]
                    dif = model[pos][0] - model[pos - 1][0]
                current += "</span><span style=background-color:" + color + ";>"

            current += line[i] + " "
            dif -= 1
        current += "</span></p>\n"
        colorFile.write(current)

    colorFile.write("</body>\n</html>")
    colorFile.close()


def colorPercentile(model, metricDict):
    """
        Assigns edit ids in model to colors by percentile based on
            metricDict. Returns a dictionary of colors.
    """
    print "Assigning colors . . ."

    # Sort by decreasing scores
    a = [(metricDict[x[1]], x[1]) for x in model]
    s = set(a)
    a = sorted(list(s), reverse=True)

    # Assign colors to nodes
    length = len(a)

    percentLen = int(length * 0.1)

    colors = {}

    # Top 1%
    for i in range(percentLen):
        colors[a[i][1]] = "darkred"
    # 1-5
    for i in range(percentLen, percentLen * 2):
        colors[a[i][1]] = "red"
    # 5-10
    for i in range(percentLen * 2, percentLen * 3):
        colors[a[i][1]] = "mediumred"
    # 10-15
    for i in range(percentLen * 3, percentLen * 4):
        colors[a[i][1]] = "lightred"
    # 15-25
    for i in range(percentLen * 4, percentLen * 5):
        colors[a[i][1]] = "pink"
    for i in range(percentLen * 5, length):
        colors[a[i][1]] = "white"

    return colors


def writeColors(title, remove, metricName, model, content, colors):
    """
        Writes the most recent revision to a .html file based on the dictionary
            colors.
        metricName will be part of the file title
    """
    print "Writing heat map . . ."

    if not os.path.isdir('heatmaps'):
        os.mkdir('heatmaps')

    if remove:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + "_rem.html", "w")
    else:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + ".html", "w")

    # Write style sheet
    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style/>\n")
    colorFile.write(
        ".white {\n\tbackground-color: white;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".pink {\n\tbackground-color: #ffcccc;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".lightred {\n\tbackground-color: #ff9999;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".mediumred {\n\tbackground-color: #ff4d4d;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".red {\n\tbackground-color: #cc0000;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".darkred {\n\tbackground-color: #990000;\n\tcolor: black;}\n")
    colorFile.write("</style>\n</head>\n")

    # Write content
    colorFile.write("<body>\n")

    content = content.split("\n")
    content = [line.split() for line in content]

    pos = 0
    dif = model[pos][0]
    color = "white"

    for line in content:
        current = "<p><span class=" + color + ">"
        for i in range(len(line)):
            if dif == 0:
                while dif == 0:
                    pos += 1
                    color = colors[model[pos][1]]
                    dif = model[pos][0] - model[pos - 1][0]
                current += "</span><span class=" + color + ">"

            current += line[i] + " "
            dif -= 1
        current += "</span></p>\n"
        colorFile.write(current)

    colorFile.write("</body>\n</html>")
    colorFile.close()


def bcolorPercentile(model, metricDict):
    """
        Assigns edit ids in model to colors by percentile based on
            metricDict. Returns a dictionary of colors.
    """
    print "Assigning colors . . ."

    # Sort by decreasing scores
    a = [(metricDict[x[1]], x[1]) for x in model]
    s = set(a)
    a = sorted(list(s), reverse=True)

    # Assign colors to nodes
    length = len(a)

    colors = {}

    # Top 1%
    for i in range(int(length * 0.01)):
        colors[a[i][1]] = "darkred"
    # 1-5
    for i in range(int(length * 0.01), int(0.05 * length)):
        colors[a[i][1]] = "red"
    # 5-15
    for i in range(int(length * 0.05), int(length * 0.15)):
        colors[a[i][1]] = "mediumred"
    # 15-25
    for i in range(int(length * 0.15), int(length * 0.25)):
        colors[a[i][1]] = "lightred"
    # 25-50
    for i in range(int(length * 0.25), int(length * 0.5)):
        colors[a[i][1]] = "pink"

    # 50-75
    for i in range(int(length * 0.5), int(length * 0.75)):
        colors[a[i][1]] = "lilac"
    # 75-85
    for i in range(int(length * 0.75), int(length * 0.85)):
        colors[a[i][1]] = "lightblue"
    # 85-95
    for i in range(int(length * 0.85), int(length * 0.95)):
        colors[a[i][1]] = "mediumblue"
    # 95-99
    for i in range(int(length * 0.95), int(length * 0.99)):
        colors[a[i][1]] = "blue"
    # Bottom 1%
    for i in range(int(length * 0.99), length):
        colors[a[i][1]] = "darkblue"

    return colors


def bwriteColors(title, remove, metricName, model, content, colors):
    """
        Writes the most recent revision to a .html file based on the dictionary
            colors.
        metricName will be part of the file title
    """
    print "Writing heat map . . ."

    if not os.path.isdir('heatmaps'):
        os.mkdir('heatmaps')

    if remove:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + "_rem.html", "w")
    else:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + ".html", "w")

    # Write style sheet
    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style/>\n")
    colorFile.write(
        ".pink {\n\tbackground-color: #ffcccc;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".lightred {\n\tbackground-color: #ff9999;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".mediumred {\n\tbackground-color: #ff4d4d;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".red {\n\tbackground-color: #cc0000;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".darkred {\n\tbackground-color: #990000;\n\tcolor: black;}\n")
    colorFile.write(
        ".lilac {\n\tbackground-color: #ccccff;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".lightblue {\n\tbackground-color: #9999ff;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".mediumblue {\n\tbackground-color: #4d4dff;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".blue {\n\tbackground-color: #0000cc;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".darkblue {\n\tbackground-color: #000099;\n\tcolor: black;}\n")
    colorFile.write("</style>\n</head>\n")

    # Write content
    colorFile.write("<body>\n")

    content = content.split("\n")
    content = [line.split() for line in content]

    pos = 0
    dif = model[pos][0]
    color = colors[model[pos][1]]

    for line in content:
        current = "<p><span class=" + color + ">"
        for i in range(len(line)):
            if dif == 0:
                while dif == 0:
                    pos += 1
                    color = colors[model[pos][1]]
                    dif = model[pos][0] - model[pos - 1][0]
                current += "</span><span class=" + color + ">"

            current += line[i] + " "
            dif -= 1
        current += "</span></p>\n"
        colorFile.write(current)

    colorFile.write("</body>\n</html>")
    colorFile.close()


def HUSLPercentile(model, metricDict):
    """
        Assigns edit ids in model to colors by percentile based on
            metricDict. Returns a dictionary of colors.
    """
    print "Assigning colors . . ."

    # Sort by decreasing scores
    a = [(metricDict[x[1]], x[1]) for x in model]
    s = set(a)
    a = sorted(list(s), reverse=True)

    # Assign colors to nodes
    length = len(a)

    colors = {}

    for i in range(int(length * 0.2)):
        colors[a[i][1]] = "c0"

    for i in range(int(length * 0.2), int(0.4 * length)):
        colors[a[i][1]] = "c1"

    for i in range(int(length * 0.4), int(length * 0.6)):
        colors[a[i][1]] = "c2"

    for i in range(int(length * 0.6), int(length * 0.8)):
        colors[a[i][1]] = "c3"

    for i in range(int(length * 0.8), int(length)):
        colors[a[i][1]] = "c4"

    return colors


def colorHUSL(title, remove, metricName, model, content, colors):
    """
        Writes the most recent revision to a .html file based on the dictionary
            colors.
        metricName will be part of the file title
    """
    print "Writing heat map . . ."

    if not os.path.isdir('heatmaps'):
        os.mkdir('heatmaps')

    if remove:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + "_rem.html", "w")
    else:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + ".html", "w")

    # Write style sheet
    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style/>\n")
    colorFile.write(
        ".c0 {\n\tbackground-color: #d7191c;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".c1 {\n\tbackground-color: #fdae61;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".c2 {\n\tbackground-color: #ffffbf;\n\tcolor: black;\n}\n")
    colorFile.write(
        ".c3 {\n\tbackground-color: #abdda4;\n\tcolor: black;\n}\n")
    colorFile.write(".c4 {\n\tbackground-color: #2b83ba;\n\tcolor: black;}\n")

    colorFile.write("</style>\n</head>\n")

    # Write content
    colorFile.write("<body>\n")

    content = content.split("\n")
    content = [line.split() for line in content]

    pos = 0
    dif = model[pos][0]
    color = colors[model[pos][1]]

    for line in content:
        current = "<p><span class=" + color + ">"
        for i in range(len(line)):
            if dif == 0:
                while dif == 0:
                    pos += 1
                    color = colors[model[pos][1]]
                    dif = model[pos][0] - model[pos - 1][0]
                current += "</span><span class=" + color + ">"

            current += line[i] + " "
            dif -= 1
        current += "</span></p>\n"
        colorFile.write(current)

    colorFile.write("</body>\n</html>")
    colorFile.close()


def metric2color(title, remove, metricName, metricDict):
    """
        Writes a heatmap of the most recent revision of title as a .html
            file in heatmaps, based on the percentile of the text according
            to metricDict.
    """
    file = title.replace(' ', '_') + ('_rem' if remove else '') + '.txt'
    content = w2g.readContent('content/' + file)
    model = w2g.readModel('models/' + file)
    #colors=bcolorPercentile(model, metricDict)
    #bwriteColors(title, remove, metricName, model, content, colors)
    colors = HUSLPercentile(model, metricDict)
    colorHUSL(title, remove, metricName, model, content, colors)


def percentileMarkup(model, metricDict):
    """
    """
    print "Assigning colors . . ."

    # Sort by decreasing scores
    a = [(metricDict[x[1]], x[1]) for x in model]
    s = set(a)
    a = sorted(list(s), reverse=True)

    # Assign colors to nodes
    length = len(a)

    colors = {}

    # Top 1%
    for i in range(int(length * 0.01)):
        colors[a[i][1]] = "#990000"
    # 1-5
    for i in range(int(length * 0.01), int(0.05 * length)):
        colors[a[i][1]] = "#cc0000"
    # 5-15
    for i in range(int(length * 0.05), int(length * 0.15)):
        colors[a[i][1]] = "ff4d4d"
    # 15-25
    for i in range(int(length * 0.15), int(length * 0.25)):
        colors[a[i][1]] = "#ff9999"
    # 25-50
    for i in range(int(length * 0.25), int(length * 0.5)):
        colors[a[i][1]] = "#ffcccc"

    # 50-75
    for i in range(int(length * 0.5), int(length * 0.75)):
        colors[a[i][1]] = "#ccccff"
    # 75-85
    for i in range(int(length * 0.75), int(length * 0.85)):
        colors[a[i][1]] = "#9999ff"
    # 85-95
    for i in range(int(length * 0.85), int(length * 0.95)):
        colors[a[i][1]] = "#4d4dff"
    # 95-99
    for i in range(int(length * 0.95), int(length * 0.99)):
        colors[a[i][1]] = "#0000cc"
    # Bottom 1%
    for i in range(int(length * 0.99), length):
        colors[a[i][1]] = "#000099"

    return colors


def writeMarkup(title, remove, metricName, model, content, colors):
    """
    """
    print "Writing heat map . . ."

    if not os.path.isdir('heatmaps'):
        os.mkdir('heatmaps')

    if remove:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + "_rem", "w")
    else:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_"), "w")

    content = content.split("\n")
    content = [line.split() for line in content]

    pos = 0
    dif = model[pos][0]
    color = colors[model[pos][1]]

    for line in content:
        current = "<p><span style=background-color:" + color + ";>"
        for i in range(len(line)):
            if dif == 0:
                while dif == 0:
                    pos += 1
                    color = colors[model[pos][1]]
                    dif = model[pos][0] - model[pos - 1][0]
                current += "</span><span style=background-color:" + color + ";>"

            current += line[i] + " "
            dif -= 1
        current += "</span></p>\n"
        colorFile.write(current)

    colorFile.close()


def getShades(model, metricDict):
    """
        Assigns a position in the color range to edits in the model, based on
            the scores in metricDict rather than percentile.
        Returns a dictionary of colors.
    """
    maxScore = max([metricDict[x[1]] for x in model])
    colors = {}
    # rbg(r,b,g) From 0-255

    for (end, edit) in model:
        color = metricDict[edit] / maxScore
        colors[edit] = int(color * NUMSHADES)

    return colors


def writeShades(title, remove, metricName, model, content, colors):
    """
        Writes the most recent revision to a .html file based on the shades in the
            dictionary, colors.
        metricName will be part of the file title
    """
    print "Writing heat map . . ."

    if not os.path.isdir('heatmaps'):
        os.mkdir('heatmaps')

    if remove:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + "_rem.html", "w")
    else:
        colorFile = open("heatmaps/" + (metricName + "_" +
                                        title).replace(" ", "_") + ".html", "w")

    # Write style sheet
    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style>\n")
    colorFile.write("p {\n\tcolor: black;\n}\n")

    # Write content
    colorFile.write("</style><body>\n")

    content = content.split("\n")
    content = [line.split() for line in content]

    pos = 0
    dif = model[pos][0]
    color = getrgb(colors[model[pos][1]])
    # colorValues = color.partition('(')[-1].rpartition(')')[0]
    # valuesList = colorValues.split(',')
    # adjustedColor = col.rgb_to_husl(int(valuesList[0]), int(valuesList[1]), int(valuesList[2]))

    for line in content:
        current = "<p><span style=background-color:" + color + ";>"
        for i in range(len(line)):
            if dif == 0:
                while dif == 0:
                    pos += 1
                    color = getrgb(colors[model[pos][1]])
                    dif = model[pos][0] - model[pos - 1][0]
                current += "</span><span style=background-color:" + color + ";>"

            current += line[i] + " "
            dif -= 1
        current += "</span></p>\n"
        colorFile.write(current)

    colorFile.write("</body>\n</html>")
    colorFile.close()


def getrgb(color):
    """
        Transforms the in color into an rgb string based on
            color's position in the color range.
    """
    crange = color / 256
    cval = color % 256

    # Loweest scores
    # White - pink
    if crange == 0:
        rgb = 'rgb(255,' + str(255 - cval) + ',255)'
    # Pink - blue
    elif crange == 1:
        rgb = 'rgb(' + str(255 - cval) + ',0,255)'
    # Blue - blue-green
    elif crange == 2:
        rgb = 'rgb(0,' + str(cval) + ',255)'
    # Blue-green - green
    elif crange == 3:
        rgb = 'rgb(0,255,' + str(255 - cval) + ')'
    # Green - yellow
    elif crange == 4:
        rgb = 'rgb(' + str(cval) + ',255,0)'
    # Yellow - red
    elif crange == 5:
        rgb = 'rgb(255,' + str(255 - cval) + ',0)'
    # Red - black
    else:
        rgb = 'rgb(' + str(255 - cval) + ',0,0)'

    return rgb


def metric2shades(title, remove, metricName, metricDict):
    """
        Writes a heatmap of the most recent revision of title as a .html
            file in heatmaps, based on the score in metricDict, rather
            than percentile.
    """
    file = title.replace(' ', '_') + ('_rem' if remove else '') + '.txt'
    content = w2g.readContent('content/' + file)
    model = w2g.readModel('models/' + file)
    colors = getShades(model, metricDict)
    writeShades(title, remove, metricName, model, content, colors)
