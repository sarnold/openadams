<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:variable name="CompanyName">Your company</xsl:variable> 

<xsl:variable name="labelDescription">Beschreibung </xsl:variable> 
<xsl:variable name="labelKeywords">Schlüsselworte</xsl:variable> 
<xsl:variable name="labelPriority">Priorität  </xsl:variable> 
<xsl:variable name="labelRisk">Risiko</xsl:variable> 
<xsl:variable name="labelComplexity">Komplexität</xsl:variable> 
<xsl:variable name="labelStatus">Status</xsl:variable> 
<xsl:variable name="labelAssigned">Zugewiesen</xsl:variable> 
<xsl:variable name="labelEffort">Aufwand</xsl:variable> 
<xsl:variable name="labelCategory">Kategorie</xsl:variable> 
<xsl:variable name="labelUsefrequency">Häufigkeit</xsl:variable> 
<xsl:variable name="labelActors">Akteure</xsl:variable> 
<xsl:variable name="labelStakeholders">Beteiligte</xsl:variable> 
<xsl:variable name="labelPrerequisites">Voraussetzungen</xsl:variable> 
<xsl:variable name="labelMainScenario">Hauptszenario</xsl:variable> 
<xsl:variable name="labelAlternativeScenario">Alternativszenario</xsl:variable> 
<xsl:variable name="labelFormat">Format</xsl:variable> 
<xsl:variable name="labelSource">Quelle</xsl:variable> 
<xsl:variable name="labelImage">Bild</xsl:variable> 
<xsl:variable name="labelContent">Inhalt</xsl:variable> 
<xsl:variable name="labelOrigin">Herkunft</xsl:variable> 
<xsl:variable name="labelRationale">Erläuterung</xsl:variable> 
<xsl:variable name="labelKind">Art</xsl:variable> 
<xsl:variable name="labelPurpose">Zweck</xsl:variable> 
<xsl:variable name="labelTestdata">Testdaten</xsl:variable> 
<xsl:variable name="labelSteps">Schritte</xsl:variable> 
<xsl:variable name="labelNotes">Hinweise</xsl:variable> 
<xsl:variable name="labelScriptURL">Skript-URL</xsl:variable> 
<xsl:variable name="labelRelatedRequirements">Zugeordnete Anforderungen</xsl:variable> 
<xsl:variable name="labelRelatedUsecases">Zugeordnete Anwendungsfälle</xsl:variable> 
<xsl:variable name="labelRelatedTestcases">Zugeordnete Testfälle</xsl:variable> 

<xsl:template name="priorityLUT">
    <xsl:param name="value" />
    <xsl:choose>
        <xsl:when test="'Expected'=normalize-space($value)">
            Erwartet
        </xsl:when>
        <xsl:when test="'Optional'=normalize-space($value)">
            Optional
        </xsl:when>
        <xsl:otherwise>
            <xsl:value-of select="$value"/>
        </xsl:otherwise>
    </xsl:choose>    
</xsl:template>

</xsl:stylesheet> 
