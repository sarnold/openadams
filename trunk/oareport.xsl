<?xml version="1.0" encoding="UTF-8"?>
<!--
XSL file to transform an openADAMS XML report into HTML.

Copyright 2008 Achim Köhler

This file is part of openADAMS.

openADAMS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 2 of the License,
or (at your option) any later version.

openADAMS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with openADAMS.  If not, see <http://www.gnu.org/licenses/>.
-->

<!-- $Id$ -->

<xsl:stylesheet version="1.0"
    xmlns="http://www.w3.org/1999/xhtml"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>
  <xsl:include href="oareportlang.xsl"/>

  <xsl:template match="/artefacts">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <meta content="text/xhtml; charset=UTF-8" http-equiv="content-type"/>
        <title>openADAMS Report</title>
        <link rel="stylesheet" type="text/css" href="oareport.css"/>
      </head>
      <body>
        <script type="text/javascript">
          <![CDATA[

function changeDisplayState (e)
{
    var num=this.id.replace(/[^[0-9]/g,'');
    var button=this.firstChild;
    var sectionDiv=document.getElementById('dynsection'+num);
    if (sectionDiv.style.display=='none'||sectionDiv.style.display=='')
    {
        sectionDiv.style.display='block';
        button.innerHTML = '-'
    }
    else
    {
        sectionDiv.style.display='none';
        button.innerHTML = '+'
    }
}

function initDynSections()
{
    var spans=document.getElementsByTagName('span');
    for(var i=0;i<spans.length-1;i++)
    {
        if(spans[i].className=='navbutton')
        {
            spans[i].style.cursor='pointer';
        }
    }
    
    var divs=document.getElementsByTagName('div');
    var sectionCounter=1;
    for(var i=0;i<divs.length-1;i++)
    {
        if(divs[i].className=='dynheader'&&divs[i+1].className=='dynsection')
        {
            var header=divs[i];
            var section=divs[i+1];
            var button=header.firstChild;
            var navbuttonclass = document.createAttribute("class");
            navbuttonclass.nodeValue = "navbutton";
            if (button!='SPAN')
            {
                divs[i].insertBefore(document.createTextNode(' '),divs[i].firstChild);
                button = document.createElement('span');
                button.appendChild(document.createTextNode("-"))
                divs[i].insertBefore(button,divs[i].firstChild);
            }
            button.setAttributeNode(navbuttonclass);
            header.style.cursor='pointer';
            header.onclick=changeDisplayState;
            header.id='dynheader'+sectionCounter;
            section.id='dynsection'+sectionCounter;
            section.style.display='block';
            sectionCounter++;
        }
    }
}

function collapseDynSections()
{
    var divs=document.getElementsByTagName('div');
    for(var i=0;i<divs.length-1;i++)
    {
        if(divs[i].className=='dynheader'&&divs[i+1].className=='dynsection')
        {
            var button=divs[i].firstChild;
            divs[i+1].style.display='none';
            button.innerHTML = '+'
        }
    }
}

function expandDynSections()
{
    var divs=document.getElementsByTagName('div');
    for(var i=0;i<divs.length-1;i++)
    {
        if(divs[i].className=='dynheader'&&divs[i+1].className=='dynsection')
        {
            var button=divs[i].firstChild;
            divs[i+1].style.display='block';
            button.innerHTML = '-'
        }
    }
}


          window.onload = initDynSections;
          ]]>
        </script>
        <a name="top"/>
        <xsl:apply-templates select="tableofcontents"/>
        <xsl:apply-templates select="contents"/>
        <a name="bottom"/>
      </body>
    </html>
  </xsl:template>

<xsl:template name="headline">
    <xsl:param name="title" />
    <xsl:param name="prefix" />
    <xsl:param name="id" />
    <h1><a>
        <xsl:attribute name="name">
        <xsl:value-of select="$prefix" />-<xsl:value-of select="normalize-space($id)"/>
        </xsl:attribute>        
        <xsl:value-of select="$prefix" />-<xsl:value-of select="normalize-space($id)"/>:
        <xsl:value-of select="$title"/>
    </a></h1>
</xsl:template>

<xsl:template name="tocline">
    <xsl:param name="title" />
    <xsl:param name="prefix" />
    <xsl:param name="id" />
    <li><a>
        <xsl:attribute name="href">#<xsl:value-of select="$prefix" />-<xsl:value-of select="normalize-space($id)"/></xsl:attribute>        
        <xsl:value-of select="$prefix" />-<xsl:value-of select="normalize-space($id)"/>:
        <xsl:value-of select="$title"/>
    </a></li>
</xsl:template>


<xsl:template match="tableofcontents">
<div id="toc">
<p id="logo"><span id="logo"><xsl:value-of select="$CompanyName"/></span></p>
<p id="toc">
<span class="navbutton" title="Expand all" onclick="expandDynSections()">+</span> 
<span class="navbutton" title="Collapse all" onclick="collapseDynSections()">-</span>
<span class="navbutton" title="Top"><a href="#top">&#8657;</a></span>
<span class="navbutton" title="Bottom"><a href="#bottom">&#8659;</a></span>
</p>

    <xsl:apply-templates select="tocfolder|tocfeature|tocusecase|tocrequirement|toccomponent|tocimage|tocsimplesection|toctestcase|toctestsuite"/>
</div>
</xsl:template>

<xsl:template match="tocfolder">
<ul class="tocfolder"><li>
    <div class="dynheader">
      <xsl:value-of select="title" />
    </div></li>
  <div class="dynsection">
    <xsl:apply-templates select="tocfolder|tocfeature|tocusecase|tocrequirement|toccomponent|tocimage|tocsimplesection|toctestcase|toctestsuite"/>
  </div>
</ul>
</xsl:template>

<xsl:template match="tocfeature">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">FT</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>

<xsl:template match="tocusecase">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">UC</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>

<xsl:template match="tocrequirement">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">RQ</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>

<xsl:template match="toccomponent">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">CM</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>

<xsl:template match="tocimage">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">IM</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>

<xsl:template match="tocsimplesection">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">SS</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>

<xsl:template match="toctestcase">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">TC</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>

<xsl:template match="toctestsuite">
<div class="tocentry">
    <xsl:call-template name="tocline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">TS</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
</div>
</xsl:template>



<xsl:template match="contents">
<div id="content">
    <xsl:apply-templates select="folder|feature|usecase|requirement|component|image|simplesection|testcase|testsuite"/>
</div>
</xsl:template>

<xsl:template match="folder">
    <div class="folder">
        <h1 class="folder">
        <xsl:attribute name="id">id<xsl:value-of select="normalize-space(id)" /></xsl:attribute >
            <xsl:value-of select="title" />
        </h1>
        <xsl:apply-templates select="folder|feature|usecase|requirement|component|image|simplesection|testcase|testsuite"/>
    </div>
</xsl:template>

  <xsl:template match="simplesection">
    <div class="simplesection">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">SS</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
        <table class="attributes">
          <tr>
            <td><xsl:value-of select="$labelKeywords"/></td>
            <td>
              <xsl:value-of select="keywords" />
            </td>
          </tr>
        </table>
        <h2 class="content"><xsl:value-of select="$labelContent"/></h2>
        <div class="content">
          <xsl:copy-of select="content"/>
        </div>
    </div>
  </xsl:template>
  
  <xsl:template match="feature">
    <div class="feature">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">FT</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
        <table class="attributes">
          <tr>
            <td><xsl:value-of select="$labelKeywords"/></td>
            <td>
              <xsl:value-of select="keywords" />
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelPriority"/></td>
            <td>
                <xsl:call-template name="priorityLUT">
                <xsl:with-param name="value" select="priority"/>
                </xsl:call-template> 
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelRisk"/></td>
            <td>
              <xsl:value-of select="risk"/>
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelStatus"/></td>
            <td>
              <xsl:value-of select="status"/>
            </td>
          </tr>
        </table>
        <h2 class="description"><xsl:value-of select="$labelDescription"/></h2>
        <div class="description">
          <xsl:copy-of select="description"/>
        </div>
        <xsl:call-template name="related_requirements"/>
        <xsl:call-template name="related_usecases"/>
    </div>
  </xsl:template>

  <xsl:template match="requirement">
    <div class="requirement">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">RQ</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
      <div class="dynsection">
        <table class="attributes">
          <tr>
            <td><xsl:value-of select="$labelKeywords"/></td>
            <td>
              <xsl:value-of select="keywords" />
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelPriority"/></td>
            <td>
              <xsl:value-of select="priority"/>
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelComplexity"/></td>
            <td>
              <xsl:value-of select="complexity"/>
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelStatus"/></td>
            <td>
              <xsl:value-of select="status"/>
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelAssigned"/></td>
            <td>
              <xsl:value-of select="assigned"/>
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelEffort"/></td>
            <td>
              <xsl:value-of select="effort"/>
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelCategory"/></td>
            <td>
              <xsl:value-of select="category"/>
            </td>
          </tr>
        </table>
        <h2 class="description"><xsl:value-of select="$labelDescription"/></h2>
        <div class="description">
          <xsl:copy-of select="description"/>
        </div>
        <h2 class="origin"><xsl:value-of select="$labelOrigin"/></h2>
        <div class="origin">
          <xsl:value-of select="origin"/>
        </div>
        <h2 class="rationale"><xsl:value-of select="$labelRationale"/></h2>
        <div class="rationale">
          <xsl:copy-of select="rationale"/>
        </div>
        <xsl:call-template name="related_usecases"/>
        <xsl:call-template name="related_testcases"/>
      </div>
    </div>
  </xsl:template>

  <xsl:template match="component">
    <div class="component">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">CM</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
        <table class="attributes">
          <tr>
            <td><xsl:value-of select="$labelKeywords"/></td>
            <td>
              <xsl:value-of select="keywords" />
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelKind"/></td>
            <td>
              <xsl:value-of select="kind"/>
            </td>
          </tr>
        </table>
        <h2 class="description"><xsl:value-of select="$labelDescription"/></h2>
        <div class="description">
          <xsl:copy-of select="description"/>
        </div>
        <xsl:call-template name="related_requirements"/>
    </div>
  </xsl:template>
  
  <xsl:template match="usecase">
    <div class="usecase">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">UC</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
      <table class="attributes">
        <tr>
          <td><xsl:value-of select="$labelKeywords"/></td>
          <td>
            <xsl:value-of select="keywords" />
          </td>
        </tr>
        <tr>
          <td><xsl:value-of select="$labelPriority"/></td>
          <td>
            <xsl:value-of select="priority"/>
          </td>
        </tr>
        <tr>
          <td><xsl:value-of select="$labelUsefrequency"/></td>
          <td>
            <xsl:value-of select="usefrequency"/>
          </td>
        </tr>
        <tr>
          <td><xsl:value-of select="$labelActors"/></td>
          <td>
            <xsl:value-of select="actors"/>
          </td>
        </tr>
        <tr>
          <td><xsl:value-of select="$labelStakeholders"/></td>
          <td>
            <xsl:value-of select="stakeholders"/>
          </td>
        </tr>
      </table>
      <h2 class="prerequisites"><xsl:value-of select="$labelPrerequisites"/></h2>
      <div class="prerequisites">
        <xsl:copy-of select="prerequisites"/>
      </div>
      <h2 class="mainscenario"><xsl:value-of select="$labelMainScenario"/></h2>
      <div class="mainscenario">
        <xsl:copy-of select="mainscenario"/>
      </div>
      <h2 class="altscenario"><xsl:value-of select="$labelAlternativeScenario"/></h2>
      <div class="altscenario">
        <xsl:copy-of select="altscenario"/>
      </div>
    </div>
  </xsl:template>

  <xsl:template match="image">
    <div class="image">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">IM</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
        <table class="attributes">
          <tr>
            <td><xsl:value-of select="$labelKeywords"/></td>
            <td>
              <xsl:value-of select="keywords" />
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelFormat"/></td>
            <td>
              <xsl:value-of select="format"/>
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelSource"/></td>
            <td>
              <xsl:value-of select="source"/>
            </td>
          </tr>
        </table>
        <h2 class="image"><xsl:value-of select="$labelImage"/></h2>
          <xsl:copy-of select="image"/>
    </div>
  </xsl:template>

  <xsl:template match="testcase">
    <div class="testcase">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">TC</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
        <table class="attributes">
          <tr>
            <td><xsl:value-of select="$labelKeywords"/></td>
            <td>
              <xsl:value-of select="keywords" />
            </td>
          </tr>
          <tr>
            <td><xsl:value-of select="$labelScriptURL"/></td>
            <td>
              <xsl:value-of select="scripturl"/>
            </td>
          </tr>
        </table>
        <h2 class="purpose"><xsl:value-of select="$labelPurpose"/></h2>
        <div class="purpose">
          <xsl:copy-of select="purpose"/>
        </div>
        <h2 class="prerequisite"><xsl:value-of select="$labelPrerequisites"/></h2>
        <div class="prerequisite">
          <xsl:copy-of select="prerequisite"/>
        </div>
        <h2 class="testdata"><xsl:value-of select="$labelTestdata"/></h2>
        <div class="testdata">
          <xsl:copy-of select="testdata"/>
        </div>
        <h2 class="steps"><xsl:value-of select="$labelSteps"/></h2>
        <div class="steps">
          <xsl:copy-of select="steps"/>
        </div>
        <h2 class="notes"><xsl:value-of select="$labelNotes"/></h2>
        <div class="notes">
          <xsl:copy-of select="notes"/>
        </div>
    </div>
  </xsl:template>

  <xsl:template match="testsuite">
    <div class="testsuite">
    <xsl:call-template name="headline">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">TS</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
        <table class="attributes">
          <tr>
            <td><xsl:value-of select="$labelKeywords"/></td>
            <td>
              <xsl:value-of select="keywords" />
            </td>
          </tr>
        </table>
        <h2 class="description"><xsl:value-of select="$labelDescription"/></h2>
        <div class="description">
          <xsl:copy-of select="description"/>
        </div>
        <xsl:call-template name="related_testcases"/>
      </div>
  </xsl:template>
  
  <xsl:template name="related_requirements">
    <h2><xsl:value-of select="$labelRelatedRequirements"/></h2>
    <xsl:choose>
      <xsl:when test="count(relations/requirement)=0">
        <xsl:text>None</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="relations/requirement"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="related_usecases">
    <h2><xsl:value-of select="$labelRelatedUsecases"/></h2>
    <xsl:choose>
      <xsl:when test="count(relations/usecase)=0">
        <xsl:text>None</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="relations/usecase"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

<xsl:template name="related_testcases">
    <h2><xsl:value-of select="$labelRelatedTestcases"/></h2>
    <xsl:choose>
      <xsl:when test="count(relations/testcase)=0">
        <xsl:text>None</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="relations/testcase"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
<xsl:template name="link_to_related">
    <xsl:param name="title" />
    <xsl:param name="prefix" />
    <xsl:param name="id" />
    <p><a>
    <xsl:attribute name="href">
    #<xsl:value-of select="$prefix" />-<xsl:value-of select="normalize-space(id)"/>
    </xsl:attribute>        
      <xsl:value-of select="$prefix" />-<xsl:value-of select="normalize-space($id)"/>:
      <xsl:value-of select="title"/>
    </a></p>
</xsl:template>

  <xsl:template match="relations/requirement">
    <xsl:call-template name="link_to_related">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">RQ</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
  </xsl:template>

  <xsl:template match="relations/usecase">
    <xsl:call-template name="link_to_related">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">UC</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
  </xsl:template>

  <xsl:template match="relations/testcase">
    <xsl:call-template name="link_to_related">
        <xsl:with-param name="title" select="title"/>
        <xsl:with-param name="prefix">TC</xsl:with-param>
        <xsl:with-param name="id" select="id" />
    </xsl:call-template> 
  </xsl:template>
  
</xsl:stylesheet>
