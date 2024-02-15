<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" version="3.0">
    <!--    <xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>-->
    <xsl:param name="values" select="(2, 3, 4, 5)"/>
    <xsl:param name="arrar" as="xs:integer"/>
    <xsl:output method="xml" indent="yes"/>

    <xsl:variable name="week" as="map(xs:string, xs:string)">
        <xsl:map>
            <xsl:map-entry key="'Mo'" select="'Monday'"/>
            <xsl:map-entry key="'Tu'" select="'Tuesday'"/>
            <xsl:map-entry key="'We'" select="'Wednesday'"/>
            <xsl:map-entry key="'Th'" select="'Thursday'"/>
            <xsl:map-entry key="'Fr'" select="'Friday'"/>
            <xsl:map-entry key="'Sa'" select="'Saturday'"/>
            <xsl:map-entry key="'Su'" select="'Sunday'"/>
        </xsl:map>
    </xsl:variable>


    <xsl:template match="*">
        <output>
            <xsl:value-of select="//person[1]"/>
            <xsl:for-each select="$values">
                <out>
                    <xsl:value-of select=". * 3"/>
                </out>
            </xsl:for-each>
        </output>
    </xsl:template>
</xsl:stylesheet>
