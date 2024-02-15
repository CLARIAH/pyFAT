<?xml version="1.0"?>
<xsl:stylesheet    xmlns:dc="http://purl.org/dc/elements/1.1/"    xmlns:dcterms="http://purl.org/dc/terms/"    xmlns:ddm="http://schemas.dans.knaw.nl/dataset/ddm-v2/"    xmlns:dcx-dai="http://easy.dans.knaw.nl/schemas/dcx/dai/"    xmlns:dcx-gml="http://easy.dans.knaw.nl/schemas/dcx/gml/"    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"    xmlns:math="http://www.w3.org/2005/xpath-functions/math"    xmlns:xs="http://www.w3.org/2001/XMLSchema"    xmlns:id-type="http://easy.dans.knaw.nl/schemas/vocab/identifier-type/"    exclude-result-prefixes="xs math" version="3.0">    
    <xsl:output indent="yes" omit-xml-declaration="yes" />        
    <xsl:template match="data">        
        <xsl:apply-templates select="json-to-xml(.)" />    
    </xsl:template>        
    <xsl:template match="map" xpath-default-namespace="http://www.w3.org/2005/xpath-functions">        
        <xsl:text>{ "data": {</xsl:text>        
        <xsl:text>"id": "</xsl:text>        
        <xsl:value-of select="/map/string[@key='id']" />        
        <xsl:text>", </xsl:text>        
        <xsl:for-each select="//array[@key='metadata']/map">            
            <xsl:text>"</xsl:text>            
            <xsl:value-of select="string[@key='id']" />            
            <xsl:text>": { </xsl:text>            
            <xsl:for-each select="array[@key='fields']/map">                
                <xsl:choose>                    
                    <xsl:when test="string[@key='name' and text()='interviewee']">                        
                        <xsl:text></xsl:text>                    
                    </xsl:when>                    
                    <xsl:when test="string[@key='name' and text()='interviewer']">                        
                        <xsl:text></xsl:text>                    
                    </xsl:when>                    
                    <xsl:when test="string[@key='name' and text()='interpreter']">                        
                        <xsl:text></xsl:text>                    
                    </xsl:when>                    
                    <xsl:when test="string[@key='name' and text()='others']">                        
                        <xsl:text></xsl:text>                    
                    </xsl:when>                    
                    <xsl:when test="string[@key='name' and text()='transcript_human']">                        
                        <xsl:text></xsl:text>                    
                    </xsl:when>                    
                    <xsl:otherwise>                        
                        <xsl:text>"</xsl:text>                        
                        <xsl:value-of select="string[@key='name']"/>                        
                        <xsl:text>": </xsl:text>                        
                        <xsl:choose>                            
                            <xsl:when test="self::map and map[@key='value']">                                
                                <xsl:text>{ "label": "</xsl:text>                                
                                <xsl:value-of select="map[@key='value']/string[@key='label']"/>                                
                                <xsl:text>", "value": "</xsl:text>                                
                                <xsl:value-of select="map[@key='value']/string[@key='value']"/>                                
                                <xsl:text>" }</xsl:text>                          
                            </xsl:when>                            
                            <xsl:when test="string[@key='value']">                                
                                <xsl:text>"</xsl:text>                                
                                <xsl:value-of select="string[@key='value']"/>                                
                                <xsl:text>"</xsl:text>                            
                            </xsl:when>                            
                            <xsl:when test="array[@key='value']">                                
                                <xsl:text>[ </xsl:text>                                
                                <xsl:for-each select="array[@key='value']/map">                                    
                                    <xsl:text>{ "label": "</xsl:text>                                    
                                    <xsl:value-of select="string[@key='label']"/>                                    
                                    <xsl:text>", "value": "</xsl:text>                                    
                                    <xsl:value-of select="string[@key='value']"/>                                    
                                    <xsl:choose>                                        
                                        <xsl:when test="position() != last()">                                            
                                            <xsl:text>" }, </xsl:text>                                        
                                        </xsl:when>                                        
                                        <xsl:otherwise>                                            
                                            <xsl:text>" } </xsl:text>                                        
                                        </xsl:otherwise>                                    
                                    </xsl:choose>                                
                                </xsl:for-each>                                
                                <xsl:text> ]</xsl:text>                            
                            </xsl:when>                            
                            <xsl:when test="string[@key='type' and text()='group'] and boolean[@key='repeatable' and text()='true']">                                
                                <xsl:text>[ </xsl:text>                                
                                <xsl:for-each select="array[@key='fields']/array">                                    
                                    <xsl:text>{ </xsl:text>                                    
                                    <xsl:for-each select="map">                                        
                                        <xsl:text>"</xsl:text>                                        
                                        <xsl:value-of select="string[@key='name']"/>                                        
                                        <xsl:choose>                                            
                                            <xsl:when test="map[@key='value']">                                                
                                                <xsl:text>": { </xsl:text>                                                
                                                <xsl:for-each select="map[@key='value']/string">                                                    
                                                    <xsl:text>"</xsl:text>                                                    
                                                    <xsl:value-of select="@key"/>                                                    
                                                    <xsl:text>": "</xsl:text>                                                    
                                                    <xsl:value-of select="."/>                                                    
                                                    <xsl:choose>                                                        
                                                        <xsl:when test="position() != last()">                                                            
                                                            <xsl:text>",</xsl:text>                                                        
                                                        </xsl:when>                                                        
                                                        <xsl:otherwise>                                                            
                                                            <xsl:text>"</xsl:text>                                                        
                                                        </xsl:otherwise>                                                    
                                                    </xsl:choose>                                                
                                                </xsl:for-each>                                                
                                                <xsl:text> }</xsl:text>                                            
                                            </xsl:when>                                            
                                            <xsl:when test="string[@key='value']">                                                
                                                <xsl:text>": "</xsl:text>                                                
                                                <xsl:value-of select="string[@key='value']"/>                                                
                                                <xsl:text>"</xsl:text>                                            
                                            </xsl:when>                                            
                                            <xsl:when test="array[@key='fields'] and string[@key='type' and text()='repeatSingleField']">                                                
                                                <xsl:text>": [ </xsl:text>                                                
                                                <xsl:for-each select="array[@key='fields']/map">                                                    
                                                    <xsl:text>"</xsl:text>                                                    
                                                    <xsl:value-of select="string[@key='value']"/>                                                    
                                                    <xsl:choose>                                                        
                                                        <xsl:when test="position() != last()">                                                            
                                                            <xsl:text>",</xsl:text>                                                        
                                                        </xsl:when>                                                        
                                                        <xsl:otherwise>                                                            
                                                            <xsl:text>"</xsl:text>                                                        
                                                        </xsl:otherwise>                                                    
                                                    </xsl:choose>                                                
                                                </xsl:for-each>                                                
                                                <xsl:text> ]</xsl:text>                                            
                                            </xsl:when>                                            
                                            <xsl:when test="array[@key='fields']">                                                
                                                <xsl:text>": { </xsl:text>                                                
                                                <xsl:for-each select="array[@key='fields']/map">                                                    
                                                    <xsl:text>"</xsl:text>                                                    
                                                    <xsl:value-of select="string[@key='name']"/>                                                    
                                                    <xsl:text>": "</xsl:text>                                                    
                                                    <xsl:value-of select="string[@key='value']"/>                                                    
                                                    <xsl:choose>                                                        
                                                        <xsl:when test="position() != last()">                                                            
                                                            <xsl:text>",</xsl:text>                                                        
                                                        </xsl:when>                                                        
                                                        <xsl:otherwise>                                                            
                                                            <xsl:text>"</xsl:text>                                                        
                                                        </xsl:otherwise>                                                    
                                                    </xsl:choose>                                                
                                                </xsl:for-each>                                                
                                                <xsl:text> }</xsl:text>                                            
                                            </xsl:when>                                            
                                            <xsl:when test="array[@key='value']/string">                                                
                                                <xsl:text>": "</xsl:text>                                                
                                                <xsl:value-of select="array[@key='value']/string"/>                                                
                                                <xsl:text>"</xsl:text>                                            
                                            </xsl:when>                                            
                                            <xsl:when test="not(array[@key='value']/string)">                                                
                                                <xsl:text>": ""</xsl:text>                                            
                                            </xsl:when>                                        
                                        </xsl:choose>                                        
                                        <xsl:choose>                                            
                                            <xsl:when test="position() != last()">                                                
                                                <xsl:text>,</xsl:text>                                            
                                            </xsl:when>                                        
                                        </xsl:choose>                                    
                                    </xsl:for-each>                                    
                                    <xsl:choose>                                        
                                        <xsl:when test="position() != last()">                                            
                                            <xsl:text>},</xsl:text>                                        
                                        </xsl:when>                                        
                                        <xsl:otherwise>                                            
                                            <xsl:text>}</xsl:text>                                        
                                        </xsl:otherwise>                                    
                                    </xsl:choose>                                
                                </xsl:for-each>                                
                                <xsl:text> ]</xsl:text>                            
                            </xsl:when>                            
                            <xsl:when test="string[@key='name' and text()='contact']">                                
                                <xsl:text>{</xsl:text>                                
                                <xsl:for-each select="array[@key='fields']/map">                                    
                                    <xsl:text>"</xsl:text>                                    
                                    <xsl:value-of select="string[@key='name']"/>                                    
                                    <xsl:text>": "</xsl:text>                                    
                                    <xsl:value-of select="string[@key='value']"/>                                    
                                    <xsl:choose>                                        
                                        <xsl:when test="position() != last()">                                            
                                            <xsl:text>",</xsl:text>                                        
                                        </xsl:when>                                        
                                        <xsl:otherwise>                                            
                                            <xsl:text>"</xsl:text>                                        
                                        </xsl:otherwise>                                    
                                    </xsl:choose>                                
                                </xsl:for-each>                                
                                <xsl:text> }</xsl:text>                            
                            </xsl:when>                            
                            <xsl:when test="array[@key='fields'] and string[text()='repeatSingleField']">                                
                                <xsl:text>[ </xsl:text>                                
                                <xsl:for-each select="array[@key='fields']/map">                                    
                                    <xsl:text>"</xsl:text>                                    
                                    <xsl:value-of select="string[@key='value']"/>                                    
                                    <xsl:choose>                                        
                                        <xsl:when test="position() != last()">                                            
                                            <xsl:text>", </xsl:text>                                        
                                        </xsl:when>                                        
                                        <xsl:otherwise>                                            
                                            <xsl:text>" </xsl:text>                                        
                                        </xsl:otherwise>                                    
                                    </xsl:choose>                                
                                </xsl:for-each>                                
                                <xsl:text> ]</xsl:text>                            
                            </xsl:when>                            
                            <xsl:when test="array[@key='fields']">                                
                                <xsl:text>{ </xsl:text>                                
                                <xsl:for-each select="array[@key='fields']/map">                                    
                                    <xsl:text>"</xsl:text>                                    
                                    <xsl:value-of select="string[@key='name']"/>                                    
                                    <xsl:text>": </xsl:text>                                    
                                    <xsl:choose>                                        
                                        <xsl:when test="string[@key='value']">                                            
                                            <xsl:text>"</xsl:text>                                            
                                            <xsl:value-of select="string[@key='value']"/>                                            
                                            <xsl:text>"</xsl:text>                                        
                                        </xsl:when>                                        
                                        <xsl:when test="array[@key='fields']">                                            
                                            <xsl:text>[ </xsl:text>                                            
                                            <xsl:for-each select="array[@key='fields']/map">                                                
                                                <xsl:text>"</xsl:text>                                                
                                                <xsl:value-of select="string[@key='value']" />                                                
                                                <xsl:choose>                                                    
                                                    <xsl:when test="position() != last()">                                                        
                                                        <xsl:text>", </xsl:text>                                                    
                                                    </xsl:when>                                                    
                                                    <xsl:otherwise>                                                        
                                                        <xsl:text>" </xsl:text>                                                    
                                                    </xsl:otherwise>                                                
                                                </xsl:choose>                                            
                                            </xsl:for-each>                                            
                                            <xsl:text>]</xsl:text>                                        
                                        </xsl:when>                                        
                                        <xsl:when test="array[@key='value']">                                            
                                            <xsl:text>"</xsl:text>                                            
                                            <xsl:value-of select="array[@key='value']/string"/>                                            
                                            <xsl:text>"</xsl:text>                                        
                                        </xsl:when>                                    
                                    </xsl:choose>                                    
                                    <xsl:choose>                                        
                                        <xsl:when test="position() != last()">                                            
                                            <xsl:text>, </xsl:text>                                        
                                        </xsl:when>                                    
                                    </xsl:choose>                                
                                </xsl:for-each>                                
                                <xsl:text> }</xsl:text>                            
                            </xsl:when>                            
                            <xsl:otherwise>""</xsl:otherwise>                        
                        </xsl:choose>                        
                        <xsl:choose>                    
                            <xsl:when test="position() != last()">                        
                                <xsl:text>, </xsl:text>                    
                            </xsl:when>                
                        </xsl:choose>                    
                    </xsl:otherwise>                
                </xsl:choose>            
            </xsl:for-each>            
            <xsl:choose>                
                <xsl:when test="position() != last()">                    
                    <xsl:text>}, </xsl:text>                
                </xsl:when>                
                <xsl:otherwise>                    
                    <xsl:text>} </xsl:text>                
                </xsl:otherwise>            
            </xsl:choose>        
        </xsl:for-each>        
        <xsl:text>}, </xsl:text>        
        <xsl:text>"file-metadata": [ </xsl:text>        
        <xsl:for-each select="//array[@key='file-metadata']/map">            
            <xsl:variable name="isExcluded" select="boolean(boolean[@key='private' and text()='true'])"/>            
            <xsl:choose>                
                <xsl:when test="$isExcluded">                    
                    <xsl:text></xsl:text>                
                </xsl:when>                
                <xsl:otherwise>                    
                    <xsl:text>{ "name": "</xsl:text>                    
                    <xsl:value-of select="string[@key='name']"/>                    
                    <xsl:text>", </xsl:text>                    
                    <xsl:text>"lastModified": "</xsl:text>                    
                    <xsl:value-of select="number[@key='lastModified']"/>                    
                    <xsl:text>", </xsl:text>                    
                    <xsl:text>"private": "</xsl:text>                    
                    <xsl:value-of select="boolean[@key='private']"/>                    
                    <xsl:text>", </xsl:text>                    
                    <xsl:choose>                        
                        <xsl:when test="map[@key='role']">                            
                            <xsl:text>"role": { "label": "</xsl:text>                            
                            <xsl:value-of select="map[@key='role']/string[@key='label']"/>                            
                            <xsl:text>", "value": "</xsl:text>                            
                            <xsl:value-of select="map[@key='role']/string[@key='value']"/>                            
                            <xsl:text>" }, </xsl:text>                        
                        </xsl:when>                    
                    </xsl:choose>                    
                    <xsl:choose>                        
                        <xsl:when test="array[@key='process']">                            
                            <xsl:text>"process": [ </xsl:text>                            
                            <xsl:for-each select="array[@key='process']/map">                                
                                <xsl:text>{ "label": "</xsl:text>                                
                                <xsl:value-of select="string[@key='label']"/>                                
                                <xsl:text>", "value": "</xsl:text>                                
                                <xsl:value-of select="string[@key='value']"/>                                
                                <xsl:text>" }</xsl:text>                                
                                <xsl:choose>                                    
                                    <xsl:when test="position() != last()">                                        
                                        <xsl:text>, </xsl:text>                                    
                                    </xsl:when>                                
                                </xsl:choose>                            
                            </xsl:for-each>                            
                            <xsl:text>] </xsl:text>                        
                        </xsl:when>                    
                    </xsl:choose>                    
                    <xsl:text>}</xsl:text>                    
                    <xsl:if test="following-sibling::map[not(boolean[@key='private' and text()='true'])]">                        
                        <xsl:text>, </xsl:text>                    
                    </xsl:if>                
                </xsl:otherwise>            
            </xsl:choose>        
        </xsl:for-each>        
        <xsl:text>] } </xsl:text>    
    </xsl:template>
</xsl:stylesheet>