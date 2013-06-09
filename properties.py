'''
Created on Apr 28, 2013

@author: ehsan
'''
from io import IOBase
from StringIO import StringIO
import pprint
import sys
import re
from configobj import ParseError
from reportlab.lib.validators import isCallable

"""
TODO:   Load/Store XML
        Use proper StringIO, BaseIO checks in the list and store methods.
        Get Name Space Property with and without expanded.
"""
class Properties(object):
    """
    Properties represents a persistent list of properties (key/value pairs of string). The properties can be read from and written to a stream.
    The values can reference the properties in the values using ${referencing-key}, the properties in the local property list can refer to the
    property defined in the default property list and vice versa.
    """

    def __init__(self, defaultProperty=None):
        """
        Creates an empty property list with defaults.
       :param defaultPropertyList: The property list that is to be used as the default property list, by default there are no default properties.
        """
        self.defaults = defaultProperty
        self.properties = {}
    
    def __getDefaultProperty(self, key):
        """
        Searches for the property key in the default property and recursively. The method return None if there is no default property.
        :param key: The property key.
        """
        if self.defaults:
            return self.defaults.getProperty(key)
        return None
    
    def getAllProps(self):
        """
        Returns a dictionary containing all the properties (key/values) and all the properties of the default properties (recursive) that are not
        in the current property object.
        """
        if self.defaults:
            resDictionary = self.defaults.getAllProps()
            resDictionary.update(self.properties)
            return resDictionary
        else:
            return self.properties
    
    def __applyFormat(self, value, formatter):
        """
        Apply the formatter on the :param value and return the result of formatter. If the formatter is None then return the :param value unchanged.
        :param value: value on which to apply format.
        :param formatter: formatter function to apply on the value before returning the result.
        """
        if formatter:
            if isCallable(formatter):
                return formatter(value)
            else:
                raise TypeError ('formatter is not callable.')
        else:
            return value
        
    def getProperty(self, key, defaultValue=None, formatter=None):
        """
        Searches for the property key in the local property list (dictionary) and returns the value un-expanded. If the :param formatter function is also provided
        then return the value after applying the formatter on the value. 
        (See :py:func:`getExpandedProperty` which returns expanded property). 
        If the key is not in the local property list then look into default property, and its default, recursively. 
        The method returns :param defaultValue if the property is not found anywhere.        
        :param key: The property key to search.
        :param defaultValue: The default value to return if property key is not found. The default value for :param defaultValue is None.
        :param formatter: The formatter function to apply on the value before returning the result. By default there is no default formatter.
        """
        if key in self.properties:
            return self.__applyFormat(self.properties[key], formatter)
        defaultPropertyValue = self.__getDefaultProperty(key)
        if defaultPropertyValue:
            return self.__applyFormat(defaultPropertyValue, formatter)
        return self.__applyFormat(defaultValue, formatter)
        
    def getExpandedProperty(self, key, defaultValue=None, formatter=None):
        """
        Does the same thing as :py:func:`getProperty` with the difference that if the value of the property contains a reference to another property
        using ${reference-key} then expand the reference key with its corresponding value in the local property list or default property list (recursive)
        before returning. If there is no referencing property then the method behaves exactly like py:func:`getProperty`.
        :param key: The property key to search.
        :param defaultValue: The default value to return if property key is not found. The default value for :param defaultValue is None.
        :param formatter: The formatter function to apply on the value before returning the result. By default there is no default formatter.
        """        
        value = self.getProperty(key, defaultValue)
        if value and re.match('.*\${([^}]+).*', value): 
            for refKey in re.findall('\$\{([^\}]+)\}', value):  #same match can occur more than once.
                refValue = self.getExpandedProperty(refKey)
                if refValue:
                    value = re.sub('\${' + refKey +'}', refValue, value)    #replaces all occurances, but its OKay.
        return self.__applyFormat(value, formatter)
        
    def list(self, out=sys.stdout):
        """
        Prints the property list out to the given stream or writer.
        :param out: The stream/writer to print the properties. This must be a derived class from IOBase or a file type. Defaults to sys.stdout 
        """
        if issubclass(out.__class__, IOBase) or issubclass(out.__class__, file) or issubclass(out.__class__, StringIO):
            pprint.pprint(self.getAllProps(), out) # pretty print the properties
        else:
            raise TypeError('Provided stream/writer is not a file or derived from :' + IOBase.__class__.__name__)
    
    @staticmethod
    def __trailingBackSlashCount(s):
        """
        Counts the number of trailing backslashes (\) in the given string.
        :param s: The input string.
        """
        backSlashCount=0
        for c in s[::-1]:
            if c=='\\':
                backSlashCount += 1
            else:
                break
        return backSlashCount
    
    @staticmethod
    def __getPropertyFromStringLine(s):
        """
        Returns the (key, value) tuple after parsing the input string :param s. The method assumes that the given string conforms to the rules for property.
        If the given string does not conforms to the property rules then throws a parse exception.
        :param s: The string to parse the property. This string should conforms to the rules of property.
        """
        precedingBackSlash = False
        key = value = ''    # By default key and value are empty strings.
        for i in range(len(s)):     # Loop through all characters in the property line.
            if s[i] == '\\':    # Encountered escape character.
                precedingBackSlash = not precedingBackSlash     # Invert precedingBackSlash as \\= needs to be parsed as \\ and = and not \ and \=.            
            elif s[i] in '=:' and not precedingBackSlash:   # Property separator encountered.
                key = s[:i]     # Key is everything before separator.
                value = s[i+1:] # Value is everything after separator.
                break;
            else:
                precedingBackSlash = False
        if key == '':   # If no key has been parsed yet, then the property does not conforms with the rules. 
            raise ParseError('Unable to parse property. Should conform to the property line rule.')
        return (key.strip(), value.strip())
    
    def load(self, inStream=sys.stdin):
        """
        Reads a property list (key/value) from input stream.
        :param inStream: input stream to read the property list. Defaults to sys.stdin
        """
        accLine = []    # Line accumulator for multiline properties.    
        for lines in inStream:
            for line in lines.split('\r'):  # inStream does not break on '\r', so we have to do it ourselves.
                if line.startswith('#') or line.startswith('!') or line.isspace():     # Ignore comments (#,!) and line comprising of whitespaces only.
                    continue
                line = line.strip()                        
                if Properties.__trailingBackSlashCount(line) % 2 == 0:  # No trailing \ or even number of trailing \, we have read one complete property.
                    accLine.append(line)
                    propertyEntry = ''.join(accLine)    # Creating a complete property line with key and value.
                    prop = Properties.__getPropertyFromStringLine(propertyEntry)    # Parse property line and get (key, value) as result or exception is thrown.
                    self.properties[prop[0]] = prop[1]
                    accLine=[]  # Reset the accumulator.
                else:
                    accLine.append(line[:-1].strip())   # Strip down white spaces before line break escape \\n            
        if accLine != []:
            raise ParseError('Invalid termination of stream, was expecting more.')                    
    
    @staticmethod
    def __mergeSingleProperties(properties):
        """
        Merge the :param properties and its default properties into a properties instance with an empty default properties, all the default properties are
        merged into the top level properties dictionary. In case of duplicate properties in the defaults chain, precedence is given to the property found
        at the topmost level.
        """
        if properties.defaults: # Has some defaults, recursively merge defaults. 
            mergedProperties = Properties.__mergeSingleProperties(properties.defaults)
            mergedProperties.properties.update(properties.properties) # merging the defaults property dictionary with the current top level dictionary.                        
            return mergedProperties
        else:   # No defaults, return a copy of the properties with default=None.
            prop = Properties()
            prop.properties = dict(properties.properties)
            return prop
        
    @staticmethod
    def mergeProperties(propertiesList=[]):
        """
        Merge list of properties :param properties and their recursive default properties into a single properties instance, giving high precedence to the properties in the
        end of the :param properties list. The returned list will have an empty default properties. 
        In case of merging a single properties, it will merge the default properties (from bottom up) and the local properties itself will be 
        merged last with the aggregated merge. See :func __mergeSingleProperties.
        """
        mergedProperties = Properties()
        for properties in propertiesList:
            mergedProperties.properties.update(Properties.__mergeSingleProperties(properties).properties)
        return mergedProperties
    
    @staticmethod
    def createPropertiesFromPropertiesFile(fName, defaultProperties=None):                
        propFile = open(fName, 'r')                                    
        prop = Properties()
        prop.load(propFile)
        return prop
            
    def loadFromXML(self, inStream=sys.stdin):
        """
        Loads all the properties in the XML document on the given input stream.
        :param inStream: input stream to read the property list in the XML document. Defaults to sys.stdin
        """
        raise NotImplementedError ('Not implemented yet.')
    
    def setProperty(self, key, value):
        """
        Puts the key/value pair in the properties list, uses the dictionary d[key]=value. Enforces the use of String for key and value.
        """
        if not key or not value or not issubclass(key.__class__, str) or not issubclass(value.__class__, str):
            raise TypeError('Key and value for the properties must be string.')
        self.properties[key] = value
    
    def store(self, out=sys.stdout):
        """
        Writes the properties according to the properties file format on the give store stream. Properties are written in the key sorted order, and in a
        format that is suitable for :func load. Properties from the defaul properties will not be written by this method.
        :param out: The stream/writer to store the properties. This must be a file or derived class from IOBase or StringIO. Defaults to sys.stdout 
        """
        if (issubclass(out.__class__, IOBase) and out.writable()) or issubclass(out.__class__, StringIO) or issubclass(out.__class__, file):            
            for k in sorted(self.properties.iterkeys()):
                out.write (unicode(k + '=' + self.properties[k] + '\n'))            
        else:
            raise TypeError('Provided stream/writer is not derived from IOBase or not is StringIO or not a writable file.')
            