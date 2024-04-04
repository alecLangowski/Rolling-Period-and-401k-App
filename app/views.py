from app import app
from flask import render_template, request, session, send_file
from math import sqrt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.colors import HexColor
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.platypus import Table
from app.dependencies import fundGroup, standardDevGraph, growth10KGraph, battingAverage, riskReturnGraph, excessReturnsGraph, betaGraph, returns, marketReturns, bondReturns, returnCombinations

#401k Calculator Classes/supporting code, must be within this document due to use of session

#calculates the total amount of a 401k given an additional employer contribution(empCont) with retirement at age 65
def totaler(total, empCont):
    try:
        for i in range(66 - session['age']):
            total = (total+((session['salary'] * ((1+session['raise'])**i))*(
                session['sr']+empCont)))*(1+session['ror'])
        return(total)
    except:
        return(0)

# switches the chosen portfolio compistion based on x% equity, y% bonds
def returnChanger(x, y):
    for i in range(35):
        try:
            returns[str(i+1)] = [((marketReturns[(session['start']-1928)+i]/100) * x) + ((bondReturns[(session['start']-1928)+i]/100)*y), False]
        except:
            returns[str(i+1)] = [((marketReturns[-(35-i)]/100) * x) + ((bondReturns[-(35-i)]/100)*y), False]

# calculates 35 years of withdrawals from the calculated retirement fund
def valueCreator(vals, total):
    try:
        for i in range(35):
            vals.append(total*session['row'])
            total = (total-vals[-1])*(1+float(returns[str(i+1)][0]))
        return vals
    except:
        return([0 for i in range(35)])

# excel spreadsheet read-in initialization for risk analysis tool
mutualFunds = fundGroup("MutualFundReturns.xlsx")
fundNames = mutualFunds.fundNames
indexes = fundGroup("IndexReturns.xlsx")
indexNames = indexes.fundNames

"""Webpage Routes"""

# home page function
@app.route("/home" , methods=["GET", "POST"])
def home():
    return(render_template("home.html"))

# route function for risk analysis page load
@app.route('/riskAnalysis', methods=["GET", "POST"])
def riskAnalysis():

    try:
        fund = request.form.get("fund")
        fundReturns = mutualFunds.indexes[fund]
    except:
        fund = "No fund selected."
        fundReturns = fund

    try:
        index = request.form.get("index")
        indexReturns = indexes.indexes[index]
    except:
        index = "No index selected."
        indexReturns = index

    if (fund != "No fund selected." and index != "No index selected."):
        # Standard Deviation Graph Variables
        justReturns = [fundReturns[i][0] for i in range(len(fundReturns))]
        standardGraph = standardDevGraph(justReturns)
        oneYr = standardGraph.data[0]
        threeYr = standardGraph.data[1]
        fiveYr = standardGraph.data[2]

        # Growth of 10K Variables
        growth10K = growth10KGraph(fundReturns, indexReturns)
        growth1 = growth10K.data[0]
        growth2 = growth10K.data[1]
        growthPeriod = growth10K.period

        # Batting Average Graph
        battingAverageGraph = battingAverage(fundReturns, indexReturns)
        battingTitles = ["Quarterly (" + str(battingAverageGraph.data[0][0]) + ") Outperformed: " + str(battingAverageGraph.data[0][-1])[:5] + "%", 
        "Yearly (" + str(battingAverageGraph.data[1][0]) + ") Outperformed: " + str(battingAverageGraph.data[1][-1])[:5] + "%",
        "Three Years (" + str(battingAverageGraph.data[2][0]) + ") Outperformed: " + str(battingAverageGraph.data[2][-1])[:5] + "%",
        "Five Years (" + str(battingAverageGraph.data[3][0]) + ") Outperformed: " + str(battingAverageGraph.data[3][-1])[:5] + "%"]
        outperformed = [battingAverageGraph.data[i][2] for i in range(4)]
        underperformed = [battingAverageGraph.data[i][1] for i in range(4)]

        # batting average table variables
        quarterlyBAT = battingAverageGraph.data[0][:3]
        yearlyBAT = battingAverageGraph.data[1][:3]
        threeBAT = battingAverageGraph.data[2][:3]
        fiveBAT = battingAverageGraph.data[3][:3]

        # Risk Return Graph
        riskReturn = riskReturnGraph(fundReturns, indexReturns)
        f1yrX = round(oneYr[0],2)
        f1yrY = round(riskReturn.fundAvgs[0],2)
        f3yrX = round(threeYr[0],2)
        f3yrY = round(riskReturn.fundAvgs[1],2)
        f5yrX = round(fiveYr[0],2)
        f5yrY = round(riskReturn.fundAvgs[2],2)
        i1yrX = round(riskReturn.standards.data[0][0],2)
        i1yrY = round(riskReturn.indexAvgs[0],2)
        i3yrX = round(riskReturn.standards.data[1][0],2)
        i3yrY = round(riskReturn.indexAvgs[1],2)
        i5yrX = round(riskReturn.standards.data[2][0],2)
        i5yrY = round(riskReturn.indexAvgs[2],2)
        if (i5yrY == -100 and f5yrY == -100):
            f5yrY = 0
            i5yrY = 0

        # Excess Returns Graph
        excessReturns = excessReturnsGraph(fundReturns, indexReturns)
        excessData = excessReturns.data

        # Excess returns table
        exQ = excessData[0]
        ex1 = excessData[1]
        ex3 = excessData[2]
        ex5 = excessData[3]
        
        # Beta Graph
        betaObject = betaGraph(fundReturns, indexReturns)
        betaOne = betaObject.data[0]
        betaThree = betaObject.data[1]
        betaFive = betaObject.data[2]

        # Period strings
        fundP = str(fundReturns[-1][2])[5:10] + "-" + str(fundReturns[-1][2])[:4] + " to " + str(fundReturns[0][2])[5:10] + "-" + str(fundReturns[0][2])[:4]
        indexP = str(indexReturns[-1][2])[5:10] + "-" + str(indexReturns[-1][2])[:4] + " to " + str(indexReturns[0][2])[5:10] + "-" + str(indexReturns[0][2])[:4]
        if len(fundReturns) <= len(indexReturns):
            comparisonP = fundP
        else:
            comparisonP=indexP
        
    # defualt values assigned if nothing selected
    else:
        oneYr,threeYr,fiveYr = ([0,0,0],[0,0,0],[0,0,0])
        growth1, growth2, growthPeriod = ([0], [0], [0,0,0,0,0,0])
        battingTitles = ["Quarterly", "Yearly", "Three Years", "Five Years"]
        outperformed = [0,0,0,0]
        underperformed = [0,0,0,0]
        f1yrX, f1yrY, f3yrX, f3yrY, f5yrX, f5yrY, i1yrX, i1yrY, i3yrX, i3yrY, i5yrX, i5yrY=(0,0,0,0,0,0,0,0,0,0,0,0)
        excessData = [0,0,0,0]
        betaOne,betaThree,betaFive = ([0,0,0], [0,0,0], [0,0,0])
        quarterlyBAT, yearlyBAT, threeBAT, fiveBAT = ([0,0,0],[0,0,0],[0,0,0],[0,0,0])
        exQ, ex1, ex3, ex5 = (0,0,0,0)
        fundP = fund
        indexP = index
        comparisonP = "No fund or index selected"

    """reportlab pdf creation"""

    report = canvas.Canvas("app/report.pdf", pagesize=letter)
    width, height = letter
    report.drawInlineImage("app\static\img\pdfLogo.png", width-200, height-90, 200, 100)
    report.setFontSize(11.5)
    report.drawString(15, height-20, fund)
    report.drawString(15, height-35, "Compared to")
    report.drawString(15, height-50, index)

    # creating colors
    blue = HexColor('#153866')
    gold = HexColor('#DEAF25')
    lightBlue = HexColor('#0977B9')
    white = HexColor("#FFFFFF")
    black = HexColor("#000000")

    #Standard Deviation Graph
    stdCanvas = Drawing(width=275, height=200)
    stdCanvas.add(String(10, 175, "Relative Standard Deviation"))
    stdPDF = VerticalBarChart()
    stdPDF._seriesCount = 3
    stdL = Legend()
    stdL.alignment = 'right'
    stdL.x = 10
    stdL.y = 70
    stdL.colorNamePairs = [(blue, "One Year"), (gold, "Three Year"), (lightBlue, "Five Year")]
    stdCanvas.add(stdL)
    stdPDF.x = 125
    stdPDF.y = 25
    stdPDF.height = 125
    stdPDF.width = 125
    stdPDF.data = [oneYr, threeYr, fiveYr]
    stdPDF.categoryAxis.categoryNames = ["avg.", "min.", "max."]
    stdPDF.bars[0].fillColor = blue
    stdPDF.bars[1].fillColor = gold
    stdPDF.bars[2].fillColor = lightBlue
    stdCanvas.add(stdPDF)
    renderPDF.draw(stdCanvas, report, 31, 500)

    #Standard Deviation Table
    stdT = Table([["Period", "Average", "Minimum", "Maximum"], ["One Year", oneYr[0], oneYr[1], oneYr[2]], ["Three Year", threeYr[0], threeYr[1], threeYr[2]], 
        ["Five Year", fiveYr[0], fiveYr[1], fiveYr[2]]])
    stdT.setStyle([('INNERGRID', (0,0), (-1,-1), 0.25, black), ('GRID', (0,0), (-1,-1), 0.25, black)])
    stdT.wrapOn(report, 125, 125)
    stdT.drawOn(report, 41, 425)

    #Beta Graph
    betaCanvas = Drawing(width=275, height = 200)
    betaCanvas.add(String(10, 175, "Rolling Period Average Beta"))
    betaPDF = VerticalBarChart()
    betaL = Legend()
    betaL.alignment = 'right'
    betaL.x = 10
    betaL.y = 70
    betaL.colorNamePairs = [(blue, "One Year"), (gold, "Three Year"), (lightBlue, "Five Year")]
    betaCanvas.add(betaL)
    betaPDF.x = 125
    betaPDF.y = 25
    betaPDF.height = 125
    betaPDF.width = 125
    betaPDF.data = [betaOne, betaThree, betaFive]
    betaPDF.categoryAxis.categoryNames = ["avg.", "min.", "max."]
    betaPDF.bars[0].fillColor = blue
    betaPDF.bars[1].fillColor = gold
    betaPDF.bars[2].fillColor = lightBlue
    betaCanvas.add(betaPDF)
    renderPDF.draw(betaCanvas, report, 306, 500)

    #Beta Table
    betaT = Table([["Period", "Average", "Minimum", "Maximum"], ["One Year", betaOne[0], betaOne[1], betaOne[2]], ["Three Year", betaThree[0], betaThree[1], betaThree[2]], 
        ["Five Year", betaFive[0], betaFive[1], betaFive[2]]])
    betaT.setStyle([('INNERGRID', (0,0), (-1,-1), 0.25, black), ('GRID', (0,0), (-1,-1), 0.25, black)])
    betaT.wrapOn(report, 125, 125)
    betaT.drawOn(report, 316, 425)

    #Batting Average
    batCanvas = Drawing(width=275, height=200)
    batCanvas.add(String(10, 175, "Batting Average"))
    batPDF = VerticalBarChart()
    batPDF.categoryAxis.style = 'stacked'
    batL = Legend()
    batL.alignment = 'right'
    batL.x = 10
    batL.y = 160
    batL.colorNamePairs = [(blue, "Underperformed"), (gold, "Outperformed")]
    batCanvas.add(batL)
    batPDF.x = 105
    batPDF.y = 25
    batPDF.height = 125
    batPDF.width = 145
    batPDF.data = [outperformed, underperformed]
    #interior bar labels
    batPDF.barLabels.boxTarget = 'mid'
    batPDF.barLabels.fillColor = white
    batPDF.barLabels.fontSize = 8
    batPDF.barLabels.fontName = 'Helvetica-Bold'
    batPDF.barLabelFormat  = '%s'
    batPDF.bars.strokeColor = white
    batPDF.categoryAxis.categoryNames = ["Quarter", "1 Year", "3 Years", "5 Years"]
    batPDF.bars[0].fillColor = gold
    batPDF.bars[1].fillColor = blue
    batCanvas.add(batPDF)
    renderPDF.draw(batCanvas, report, 31, 200)

    #Batting Average
    try:
        batT = Table([["Period", "Total #", "# Underperf.", "# Outperf.", "Outperf. %"], ["Quarterly", quarterlyBAT[0], quarterlyBAT[1], quarterlyBAT[2], str(battingAverageGraph.data[0][-1])[:5] + "%"],
        ["One Year", yearlyBAT[0], yearlyBAT[1], yearlyBAT[2], str(battingAverageGraph.data[1][-1])[:5] + "%"], ["Three Years", threeBAT[0], threeBAT[1], threeBAT[2], str(battingAverageGraph.data[2][-1])[:5] + "%"],
        ["Five Years", fiveBAT[0], fiveBAT[1], fiveBAT[2], str(battingAverageGraph.data[3][-1])[:5] + "%"]])
    except:
        batT = Table([["Period", "Total #", "# Underperf.", "# Outperf.", "Outperf. %"], ["Quarterly", quarterlyBAT[0], quarterlyBAT[1], quarterlyBAT[2], "0%"],
        ["One Year", yearlyBAT[0], yearlyBAT[1], yearlyBAT[2], "0%"], ["Three Years", threeBAT[0], threeBAT[1], threeBAT[2], "0%"],
        ["Five Years", fiveBAT[0], fiveBAT[1], fiveBAT[2], "0%"]])
    batT.setStyle([('INNERGRID', (0,0), (-1,-1), 0.25, black), ('GRID', (0,0), (-1,-1), 0.25, black)])
    batT.wrapOn(report, 125, 125)
    batT.drawOn(report, 41, 100)

    #Excess Returns Graph
    excCanvas = Drawing(width=275, height=200)
    excCanvas.add(String(10, 175, "Excess Returns"))
    excPDF = VerticalBarChart()
    excPDF.x = 75
    excPDF.y = 25
    excPDF.height = 125
    excPDF.width = 170
    excPDF.data = [excessData]
    excPDF.categoryAxis.categoryNames = ["Quarter", "1 Year", "3 Years", "5 Years"]
    excPDF.bars[0].fillColor = gold
    excCanvas.add(excPDF)
    renderPDF.draw(excCanvas, report, 306, 200)

    #Excess Returns Table
    excT = Table([["Period", "Excess Return"], ["Quarter", excessData[0]], ["One Year", excessData[1]], ["Three Years", excessData[2]], ["Five Years", excessData[3]]])
    excT.setStyle([('INNERGRID', (0,0), (-1,-1), 0.25, black), ('GRID', (0,0), (-1,-1), 0.25, black)])
    excT.wrapOn(report, 125, 125)
    excT.drawOn(report, 380, 100)

    #Second Page Header
    report.showPage()
    report.drawInlineImage("app\static\img\pdfLogo.png", width-200, height-90, 200, 100)
    report.setFontSize(11.5)
    report.drawString(15, height-20, fund)
    report.drawString(15, height-35, "Compared to")
    report.drawString(15, height-50, index)

    #Risk Return Profile Graph
    rrCanvas = Drawing(width=400, height=200)
    rrCanvas.add(String(10,175, "Risk Return Profile (Std. Deviation - X & Avg. Return - Y)"))
    rrPDF = LinePlot()
    rrL1 = Legend()
    rrL1.alignment = 'right'
    rrL1.x = 10
    rrL1.y = 165
    rrL1.colorNamePairs = [(blue, "Fund")]
    rrCanvas.add(rrL1)
    rrL2 = Legend()
    rrL2.alignment = 'right'
    rrL2.x = 75
    rrL2.y = 165
    rrL2.colorNamePairs = [(gold, "Index")]
    rrCanvas.add(rrL2)
    rrPDF.x = 65
    rrPDF.y = 25
    rrPDF.width = 300
    rrPDF.height = 125
    rrPDF.data = [((f1yrX, f1yrY), (f3yrX, f3yrY), (f5yrX, f5yrY)), ((i1yrX, i1yrY), (i3yrX, i3yrY), (i5yrX, i5yrY))]
    rrPDF.lines[0].strokeColor = blue
    rrPDF.lines[0].symbol = makeMarker("Circle")
    rrPDF.lines[1].strokeColor = gold
    rrPDF.lines[1].symbol = makeMarker("Circle")
    rrCanvas.add(rrPDF)
    renderPDF.draw(rrCanvas, report, 31, 500)

    #Risk Return Profile Table
    report.drawString(31, 480, "Fund")
    report.drawString(271, 480, "Index")
    fundT = Table([["Period", "Avg Return", "Standard Dev"], ["One Year", f1yrX, f1yrY], ["Three Years", f3yrX, f3yrY], ["Five Years", f5yrX, f5yrY]])
    fundT.setStyle([('INNERGRID', (0,0), (-1,-1), 0.25, black), ('GRID', (0,0), (-1,-1), 0.25, black)])
    fundT.wrapOn(report, 125, 125)
    fundT.drawOn(report, 36, 400)
    indexT = Table([["Period", "Avg Return", "Standard Dev"], ["One Year", i1yrX, i1yrY], ["Three Years", i3yrX, i3yrY], ["Five Years", i5yrX, i5yrY]])
    fundT.setStyle([('INNERGRID', (0,0), (-1,-1), 0.25, black), ('GRID', (0,0), (-1,-1), 0.25, black)])
    fundT.wrapOn(report, 125, 125)
    fundT.drawOn(report, 276, 400)

    
    #Growth 10K Graph
    growCanvas = Drawing(width=275, height=200)
    growCanvas.add(String(10, 175, "Growth of 10K"))
    growPDF = HorizontalLineChart()
    growL1 = Legend()
    growL1.alignment = 'right'
    growL1.x = 10
    growL1.y = 165
    growL1.colorNamePairs = [(blue, "Fund")]
    growCanvas.add(growL1)
    growL2 = Legend()
    growL2.alignment = 'right'
    growL2.x = 75
    growL2.y = 165
    growL2.colorNamePairs = [(gold, "Index")]
    growCanvas.add(growL2)
    growPDF.x = 50
    growPDF.y = 25
    growPDF.height = 125
    growPDF.width = 200
    growPDF.data = [growth1, growth2]
    growPDF.lines[0].strokeColor = blue
    growPDF.lines[1].strokeColor = gold
    growPDF.strokeColor = black
    growCanvas.add(growPDF)
    renderPDF.draw(growCanvas, report, 31, 200)

    #disclaimer
    report.setFontSize(8)
    report.drawCentredString(width/2, 150, "Advanced Capital Group (ACG) is a Registered Investment Advisor (RIA) domiciled in the state of Minnesota")
    report.drawCentredString(width/2, 140, "and subject to the Investment Advisor Act of 1940. This information is not a recommendation to sell, hold")
    report.drawCentredString(width/2, 130, "or buy any security. All investments carry risk of loss and may lose value and past performance is not a")
    report.drawCentredString(width/2, 120, "guarantee of future results. Investment products are not FDIC insured, and FDIC and SIPC insurance coverage")
    report.drawCentredString(width/2, 110, "do not protect investors from market losses due to fluctuation in market values. As an RIA, ACG does not")
    report.drawCentredString(width/2, 100, "provide tax advice or legal services. This material is for educational purposes only and does not constitute")
    report.drawCentredString(width/2, 90, "an investment advisory agreement. This document is the property of Advanced Capital Group, Inc. CRD")

    report.save()
        
    
    # variable passing to html page
    return(render_template("riskAnalysis.html", fundNames=fundNames, indexNames=indexNames, fund=fund, index=index, fundReturns=fundReturns, indexReturns=indexReturns,
        oneYr=oneYr, threeYr=threeYr, fiveYr=fiveYr, growth1=growth1, growth2=growth2, growthPeriod=growthPeriod, battingTitles=battingTitles , outperformed=outperformed,
        underperformed=underperformed, f1yrX=f1yrX, f1yrY=f1yrY, f3yrX=f3yrX, f3yrY=f3yrY, f5yrX=f5yrX, f5yrY=f5yrY, i1yrX=i1yrX, i1yrY=i1yrY, i3yrX=i3yrX, i3yrY=i3yrY,
        i5yrX=i5yrX, i5yrY=i5yrY, excessData=excessData, betaOne=betaOne, betaThree=betaThree, betaFive=betaFive, quarterlyBAT=quarterlyBAT, yearlyBAT=yearlyBAT,
        threeBAT=threeBAT, fiveBAT=fiveBAT, exQ=exQ, ex1=ex1, ex3=ex3, ex5=ex5, fundP=fundP, indexP=indexP, comparisonP=comparisonP))
         
# 401k Calculator Route Function
@app.route('/401kCalculator', methods=['POST', 'GET'])
def calculator():

    if request.method == "POST":

        # changes the starting year of retirement calculations
        if 'Starting Year' in request.form and request.form['Starting Year'] != '':
            try:
                # actual changing of start year
                if int(request.form['Starting Year']) > 1927 and int(request.form['Starting Year']) < 1988:
                    session['start'] = int(request.form['Starting Year'])

                #changing of returns
                for i in range(35):

                    # flat 5% selected
                    if session['portfolio'][2] == 'a':
                        returns[str(i+1)] = [0.05, False]

                    # 100% ---- selected
                    elif session['portfolio'][2] == '0':

                        if session['portfolio'][5] == 'E':
                            returns[str(i+1)] = [((marketReturns[(session['start']-1928)+i]/100)), False]
                        else:
                            returns[str(i+1)] = [((bondReturns[(session['start']-1928)+i]/100)), False]

                    # any other combination selected
                    else:
                        returns[str(i+1)] = [((marketReturns[(session['start']-1928)+i]/100)*(int(session['portfolio'][0])/10)) + 
                        ((bondReturns[(session['start']-1928)+i]/100)*(int(session['portfolio'][12])/10)), False]

                # human readable interpretation of the retirement window is created
                session['window'] = str(session['start']) + '-' + str(session['start']+34)
            except:
                pass
        
        # handles each button that changes portfolio composition
        if request.form['submitButton'] == 'Flat 5% Rate of Return':
            for i in range(35):
                returns[str(i+1)] = [0.05, False]
            session['portfolio'] = 'Flat 5% Rate of Return'
        elif request.form['submitButton'] == '100% Equity Returns':
            # return changer is called to recalculate returns
            returnChanger(1, 0)
            # human readable portfolio composition is stored
            session['portfolio'] = '100% Equity Returns'
        elif request.form['submitButton'] == '100% Bond Returns':
            returnChanger(0, 1)
            session['portfolio'] = '100% Bond Returns'
        elif request.form['submitButton'] == '90% Equity, 10% Bonds':
            returnChanger(0.9, 0.1)
            session['portfolio'] = '90% Equity, 10% Bonds'
        elif request.form['submitButton'] == '80% Equity, 20% Bonds':
            returnChanger(0.8, 0.2)
            session['portfolio'] = '80% Equity, 20% Bonds'
        elif request.form['submitButton'] == '70% Equity, 30% Bonds':
            returnChanger(0.7, 0.3)
            session['portfolio'] = '70% Equity, 30% Bonds'
        elif request.form['submitButton'] == '60% Equity, 40% Bonds':
            returnChanger(0.6, 0.4)
            session['portfolio'] = '60% Equity, 40% Bonds'
        elif request.form['submitButton'] == '50% Equity, 50% Bonds':
            returnChanger(0.5, 0.5)
            session['portfolio'] = '50% Equity, 50% Bonds'
        elif request.form['submitButton'] == '40% Equity, 60% Bonds':
            returnChanger(0.4, 0.6)
            session['portfolio'] = '40% Equity, 60% Bonds'
        elif request.form['submitButton'] == '30% Equity, 70% Bonds':
            returnChanger(0.3, 0.7)
            session['portfolio'] = '20% Equity, 80% Bonds'
        elif request.form['submitButton'] == '20% Equity, 80% Bonds':
            returnChanger(0.2, 0.8)
            session['portfolio'] = '20% Equity, 80% Bonds'
        elif request.form['submitButton'] == '10% Equity, 90% Bonds':
            returnChanger(0.1, 0.9)
            session['portfolio'] = '10% Equity, 90% Bonds'

        if request.form["submitButton"] == "Calculate":

            #Specifying a rate of return for a given year
            if request.form['year'] != '' and request.form['return'] != '':
                try:
                    returns[str(int(request.form['year']) - session["start"]+1)] = [float(request.form['return'])/100, True]
                except:
                    session["start"] = 1987
                    returns[str(int(request.form['year']) - session["start"]+1)] = [float(request.form['return'])/100, True]

            if request.form['Starting Salary'] != '':
                try:
                    session['salary'] = float(request.form['Starting Salary'].replace(",", ""))
                except:
                    pass

            if request.form['Annual Raise'] != '':
                if '0.' in request.form['Annual Raise']:
                    session['raise'] = float(request.form['Annual Raise'])
                else:
                    try:
                        session['raise'] = float(request.form['Annual Raise'])/100
                    except:
                        pass

            if request.form['Saving Rate'] != '':
                if '0.' in request.form['Saving Rate']:
                    session['sr'] = float(request.form['Saving Rate'])
                else:
                    try:
                        session['sr'] = float(request.form['Saving Rate'])/100
                    except:
                        pass

            if request.form['Rate of Return'] != '':
                if '0.' in request.form['Rate of Return']:
                    session['ror'] = float(request.form['Rate of Return'])
                else:
                    try:
                        session['ror'] = float(request.form['Rate of Return'])/100
                    except:
                        pass

            if request.form['Starting Age'] != '':
                try:
                    session['age'] = int(request.form['Starting Age'])
                except:
                    pass

            if request.form['Rate of Withdrawal'] != '':
                if '0.' in request.form['Rate of Withdrawal']:
                    session['row'] = float(request.form['Rate of Withdrawal'])
                else:
                    try:
                        session['row'] = float(request.form['Rate of Withdrawal'])/100
                    except:
                        pass
            
    # pension is calculated if applicable
    try:
        pension = [((((session['salary']*((session['raise']+1)**(65-session['age'])))+(session['salary']*((session['raise']+1) 
            **(64-session['age'])))+(session['salary']*((session['raise']+1)**(63-session['age']))))/3)*0.02)*35 for i in range(35)]
    except:
        pension = [0 for i in range(35)]

    # this recursive method iterates through possible return scenarios and compares average withdrawal with the corresponding pension plan(hence the placement)
    # the recursive step finds the least amount of additional employer contribution towards the 401k in order to equate average withdrawal to the pension
    def avgContribution(session, scenarios):
        # recursive helper function that increases and stores employer contribution % and returns that % when average withdrawal >= pension payment
        def helper(session, n, sequence):
            total = 0
            # try except clause calculates the total amount of the corresponding 401k
            try:
                for i in range(66-session['age']):
                    total = (
                        total + ((session['salary']*((1+session['raise'])**i))*(session['sr']+n)))*(1+session['ror'])
            except:
                pass
            
            # vals intitialized and substantiated to hold annual withdrawal
            vals = []
            try:
                for i in range(35):
                    vals.append(total*session['row'])
                    total = (total-vals[-1])*(1+(float(sequence[i])/100))
            except:
                vals = [0 for i in range(35)]
            
            # checks if average withdrawal >= pension payment, if not the recursive step is executed
            if (sum(vals)/len(vals)) < pension[0]:
                return(helper(session, n+0.01, sequence))

            # if not, the minimum additional employer contribution to equate the 401k to the pension plan for this SINGLE scenario is returned
            return(n)

        # employer contribution list is initialized to hold all of the n-values that will be returned from the helper function
        employerContribution = []
        for i in range(len(scenarios)):
            employerContribution.append(helper(session, 0.01, scenarios[i]))

        # the average minimum addtional employer contribution to equate the possible 401k's to the pension plan is calculated
        mean = int((sum(employerContribution) / len(employerContribution))*100)

        # the average and standard deviation are returns from employerContribution
        return([mean, int(sqrt((sum([(val-(mean/100))**2 for val in employerContribution]))/len(employerContribution))*1000)/1000])

    # 401k is calculated from given data
    session['total'] = 0
    session['total'] = totaler(session['total'], 0)

    # graph values for the regular 401k are calculated
    regVals = []
    retTotal = session['total']
    regVals = valueCreator(regVals, retTotal)

    # following 11 categories calculate the minimum average employer contribution required for each portfolio weight to make the average 401k equate the pension plan
    # essentially we are doing this to get an average over all portfolio weights for employer contribution, and a worst case scenario and a best case one
    marketAvgCont, marketStdDev = avgContribution(session, returnCombinations['market'])
    marketTotal = 0
    marketTotal = totaler(marketTotal, marketAvgCont/100)
    marketVals = []
    marketVals = valueCreator(marketVals, marketTotal)

    bondAvgCont, bondStdDev = avgContribution(session, returnCombinations['bonds'])
    bondTotal = 0
    bondTotal = totaler(bondTotal, bondAvgCont/100)
    bondVals = []
    bondVals = valueCreator(bondVals, bondTotal)

    M90B10cont, M90B10stdDev = avgContribution(session, returnCombinations['90M10B'])
    M90B10total = 0
    M90B10total = totaler(M90B10total, M90B10cont/100)
    M90B10vals = []
    M90B10vals = valueCreator(M90B10vals, M90B10total)

    M80B20cont, M80B20stdDev = avgContribution(session, returnCombinations['80M20B'])
    M80B20total = 0
    M80B20total = totaler(M80B20total, M80B20cont/100)
    M80B20vals = []
    M80B20vals = valueCreator(M80B20vals, M80B20total)

    M70B30cont, M70B30stdDev = avgContribution(session, returnCombinations['70M30B'])
    M70B30total = 0
    M70B30total = totaler(M70B30total, M70B30cont/100)
    M70B30vals = []
    M70B30vals = valueCreator(M70B30vals, M70B30total)

    M60B40cont, M60B40stdDev = avgContribution(session, returnCombinations['60M40B'])
    M60B40total = 0
    M60B40total = totaler(M60B40total, M60B40cont/100)
    M60B40vals = []
    M60B40vals = valueCreator(M60B40vals, M60B40total)

    M50B50cont, M50B50stdDev = avgContribution(session, returnCombinations['50M50B'])
    M50B50total = 0
    M50B50total = totaler(M50B50total, M50B50cont/100)
    M50B50vals = []
    M50B50vals = valueCreator(M50B50vals, M50B50total)

    M40B60cont, M40B60stdDev = avgContribution(session, returnCombinations['40M60B'])
    M40B60total = 0
    M40B60total = totaler(M40B60total, M40B60cont/100)
    M40B60vals = []
    M40B60vals = valueCreator(M40B60vals, M40B60total)

    M30B70cont, M30B70stdDev = avgContribution(session, returnCombinations['30M70B'])
    M30B70total = 0
    M30B70total = totaler(M30B70total, M30B70cont/100)
    M30B70vals = []
    M30B70vals = valueCreator(M30B70vals, M30B70total)

    M20B80cont, M20B80stdDev = avgContribution(session, returnCombinations['20M80B'])
    M20B80total = 0
    M20B80total = totaler(M20B80total, M20B80cont/100)
    M20B80vals = []
    M20B80vals = valueCreator(M20B80vals, M20B80total)

    M10B90cont, M10B90stdDev = avgContribution(session, returnCombinations['10M90B'])
    M10B90total = 0
    M10B90total = totaler(M10B90total, M10B90cont/100)
    M10B90vals = []
    M10B90vals = valueCreator(M10B90vals, M10B90total)

    # the above variables are put into data structures so that they may be operated on
    contributionList = [marketAvgCont, bondAvgCont, M90B10cont, M80B20cont, M70B30cont,M60B40cont, M50B50cont, M40B60cont, M30B70cont, M20B80cont, M10B90cont]
    contributionCorrespondence = {str(marketAvgCont): ('100% Equity', marketStdDev), str(bondAvgCont): ('100% Bonds', bondStdDev), 
        str(M90B10cont): ('90% Equity 10% Bonds', M90B10stdDev), str(M80B20cont): ('80% Equity 20% Bonds', M80B20stdDev), str(M70B30cont): ('70% Equity 30% Bonds', M70B30stdDev), 
        str(M60B40cont): ('60% Equity 40% Bonds', M60B40stdDev), str(M50B50cont): ('50% Equity 50% Bonds', M50B50stdDev), str(M40B60cont): ('40% Equity 60% Bonds', M40B60stdDev), 
        str(M30B70cont): ('30% Equity 70% Bonds', M30B70stdDev), str(M20B80cont): ('20% Equity 80% Bonds', M20B80stdDev), str(M10B90cont): ('10% Equity 90% Bonds', M10B90stdDev)}

    # the magic number is the average employer contribution required from all portfolios to equate the 401k to the pension
    # essentially this is the reccomended employer contribution
    magicNum = (int((sum(contributionList)/11)*100))/100
    magicTotal = 0
    magicTotal = totaler(magicTotal, magicNum/100)
    magicVals = []
    magicVals = valueCreator(magicVals, magicTotal)

    # this represents the best case scenario based off of the calculated portfolio weights
    minCont = min(contributionList)
    minPortfolio, minStdDev = contributionCorrespondence[str(minCont)]
    minTotal = 0
    minTotal = totaler(minTotal, minCont/100)
    minVals = []
    minVals = valueCreator(minVals, minTotal)
    
    # this represents the worst case scenario, or the maximum employer contribution
    maxCont = max(contributionList)
    maxPortfolio, maxStdDev = contributionCorrespondence[str(maxCont)]
    maxTotal = 0
    maxTotal = totaler(maxTotal, maxCont/100)
    maxVals = []
    maxVals = valueCreator(maxVals, maxTotal)

    # form fields are transformed into a human readable form
    try:
        salary = "{:,}".format((int(session['salary']*100))/100)
    except:
        salary = 0
    try:
        payRaise = session['raise']*100
    except:
        payRaise = 0
    try:
        sr = session['sr']*100
    except:
        sr = 0
    try:
        ror = session['ror']*100
    except:
        ror = 0
    try:
        age = session['age']
    except:
        age = 0
    try:
        row = session['row']*100
    except:
        row = 0
    try:
        start = str(session['start'])
    except:
        start = '1987'
    try:
        window = session['window']
    except:
        window = '1987-2021'
    portfolio = ''
    try:
        portfolio = session['portfolio']
    except:
        portfolio = 'Flat 5% Rate of Return'

    # checks if any returns have been changed within the recent load and stores them in a human readable form ready to be displayed
    changedReturns = ''
    for key in returns:
        if returns[key][1] == True:
            if len(changedReturns) == 0:
                changedReturns = changedReturns + 'Year ' + str(int(key) + int(start)-1) + ': ' + str(int(returns[key][0]*100)) + '%'
            else:
                changedReturns = changedReturns + ', Year ' + str(int(key) + int(start)-1) + ': ' + str(int(returns[key][0]*100)) + '%'

    tLabels = []
    for i in range(35):
        tLabels.append(int(start) + i)

    # variables are passed and html page is intitialized
    return render_template('401kCalculator.html', form_data=session, regVals=regVals, pension=pension, minVals=minVals, minCont=minCont, minPortfolio=minPortfolio, 
        minStdDev=minStdDev, maxVals=maxVals, maxCont=maxCont, maxPortfolio=maxPortfolio, maxStdDev=maxStdDev, magicVals=magicVals, magicNum=magicNum, 
        portfolio=portfolio, salary=salary, payRaise=payRaise, sr=sr, ror=ror, age=age, row=row, changedReturns=changedReturns, start=start, window=window, tLabels=tLabels)

@app.route("/download")
def reportPDF():
    return(send_file("report.pdf", as_attachment=True))