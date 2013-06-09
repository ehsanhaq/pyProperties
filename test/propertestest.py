'''
Created on Apr 28, 2013

@author: ehsan
'''
import unittest

from reportlab.lib.validators import isCallable
import io
import StringIO
import os
import sys
import properties as p
from mock import patch

"""
TODO: Unittests for list and store.
"""
class PropertiesTest(unittest.TestCase):

    @staticmethod
    def getInputStream(inputString):        
        return io.BytesIO(bytearray(inputString))
    
    @staticmethod
    def getOutputStream():
        return StringIO.StringIO()
    
    @staticmethod
    def __getExceptionFromCall(func, *args, **kwargs):
        if not isCallable(func):
            return RuntimeError('First argument must be callable.')
        try:
            func(*args, **kwargs)        
        except Exception, e:            
            return e        
        return RuntimeError('Function did not raise any exception.')
        
    def testCreation(self):        
        prop1 = p.Properties()
        self.assertNotEqual(prop1, None, 'Unable to create empty property instance.')
        prop2 = p.Properties(prop1)
        self.assertNotEqual(prop2, None, 'Unable to create property instance with default properties.')
        self.assertEqual(prop2.defaults, prop1)
         
    def testGetPropertyNonExistingProperties(self):
        prop = p.Properties()
        self.assertEqual(prop.getProperty('key'), None)
        prop.setProperty('key', 'value')
        self.assertEqual(prop.getProperty('key1'), None)
        self.assertEqual(prop.getProperty('key2'), None)
             
    def testGetPropertyExistingProperties(self):
        prop = p.Properties()        
        prop.setProperty('key1', 'value1')
        prop.setProperty('key2', 'value2')
        prop.setProperty('key3', 'value2')
        self.assertEqual(prop.getProperty('key1'), 'value1')
        self.assertEqual(prop.getProperty('key2'), 'value2')
        self.assertEqual(prop.getProperty('key3'), 'value2')
     
    def testGetPropertyDefaultProperty(self):
        prop = p.Properties()
        prop.setProperty('key1', 'value1')
        self.assertEqual(prop.getProperty('key1', 'valueX'), 'value1')
        self.assertEqual(prop.getProperty('key2', 'value2'), 'value2')
        
    def testSetPropertyOverrideLocalAndDefault(self):
        prop = p.Properties()
        prop.setProperty('key', 'value')
        prop.setProperty('key1', 'value1')
        prop.setProperty('key', 'value-updated')
        self.assertEqual(prop.getProperty('key'), 'value-updated')
        prop1 = p.Properties(prop)
        prop1.setProperty('key', 'value-updated-again')
        self.assertEqual(prop1.getProperty('key'), 'value-updated-again')            
            
    def testSetPropertyNonStringKeyValue(self):
        prop = p.Properties()        
        self.assertTrue(PropertiesTest.__getExceptionFromCall(prop.setProperty, None, 'value').__class__ == TypeError)
        self.assertTrue(PropertiesTest.__getExceptionFromCall(prop.setProperty, 'key', None).__class__ == TypeError)
        self.assertTrue(PropertiesTest.__getExceptionFromCall(prop.setProperty, 'key', 1).__class__ == TypeError)
        self.assertTrue(PropertiesTest.__getExceptionFromCall(prop.setProperty, 'key', 1.3).__class__ == TypeError)
        self.assertTrue(PropertiesTest.__getExceptionFromCall(prop.setProperty, 'key', prop).__class__ == TypeError)
           
    def testGetPropertyExpandedBehavesLikeGetProperty(self):
        prop = p.Properties()
        self.assertEqual(prop.getExpandedProperty('key'), None)
        prop.setProperty('key', 'value')
        self.assertEqual(prop.getExpandedProperty('key1'), None)
        self.assertEqual(prop.getExpandedProperty('key2'), None)
        prop.setProperty('key1', 'value1')
        prop.setProperty('key2', 'value2 ${not-found-ref}')        
        self.assertEqual(prop.getExpandedProperty('key1'), 'value1')        
        self.assertEqual(prop.getExpandedProperty('key2'), 'value2 ${not-found-ref}')
        
    def testGetPropertyExpandedWithExpansions(self):
        prop = p.Properties()        
        prop.setProperty('key', 'value')        
        prop.setProperty('key1', 'value1')
        prop.setProperty('key2', 'value2 ${key1}')        
        self.assertEqual(prop.getExpandedProperty('key1'), 'value1')        
        self.assertEqual(prop.getExpandedProperty('key2'), 'value2 value1')
        prop1 = p.Properties(prop)
        prop1.setProperty('key11', 'value11')
        prop1.setProperty('key21', 'value2 ${key1}')
        prop1.setProperty('key22', 'value22 ${key2}')
        prop1.setProperty('key23', 'value23 ${key22} ${key1} ${not-found-ref}')
        self.assertEqual(prop1.getExpandedProperty('key11'), 'value11')        
        self.assertEqual(prop1.getExpandedProperty('key21'), 'value2 value1')
        self.assertEqual(prop1.getExpandedProperty('key22'), 'value22 value2 value1')
        self.assertEqual(prop1.getExpandedProperty('key23'), 'value23 value22 value2 value1 value1 ${not-found-ref}')    
            
    def testGetPropertyLoadSingleLinePropertiesSimple(self):
        prop = p.Properties()
        inputString = 'key1=value1\nkey2=value2 \n key3 = value3 \r\n \tkey4\t=\f \t value4 \t\n key5 = "  value5\t"'        
        prop.load(PropertiesTest.getInputStream(inputString))
        self.assertEqual(prop.getProperty('key1'), 'value1')
        self.assertEqual(prop.getProperty('key2'), 'value2')
        self.assertEqual(prop.getProperty('key3'), 'value3')
        self.assertEqual(prop.getProperty('key4'), 'value4')
        self.assertEqual(prop.getProperty('key5'), '"  value5\t"')
            
        # Same tests as above but with : instead of =
        prop = p.Properties()
        inputString = 'key1:value1\nkey2:value2 \n key3 : value3 \r\n \tkey4\t:\f \t value4 \t\n key5 : "  value5\t"'        
        prop.load(PropertiesTest.getInputStream(inputString))
        self.assertEqual(prop.getProperty('key1'), 'value1')
        self.assertEqual(prop.getProperty('key2'), 'value2')
        self.assertEqual(prop.getProperty('key3'), 'value3')
        self.assertEqual(prop.getProperty('key4'), 'value4')
        self.assertEqual(prop.getProperty('key5'), '"  value5\t"')
        
    def testGetPropertyLoadSingleLinePropertiesComplex(self):
        prop = p.Properties()
        inputString = 'key1=\nkey2==value2 \n key3\= = v=a:l:u=e:3 \r\n \tkey\t4=\f \t val\tu\te4 \t\n ke\=y\:\t\f5\t\f : "  value5\t"'        
        prop.load(PropertiesTest.getInputStream(inputString))
        self.assertEqual(prop.getProperty('key1'), '')
        self.assertEqual(prop.getProperty('key2'), '=value2')
        self.assertEqual(prop.getProperty('key3\='), 'v=a:l:u=e:3')
        self.assertEqual(prop.getProperty('key\t4'), 'val\tu\te4')
        self.assertEqual(prop.getProperty('ke\=y\:\t\f5'), '"  value5\t"')                 
       
    def testGetPropertyLoadMultiLineProperties(self):
        prop = p.Properties()
        inputString = 'key1\\\n= value1 \n key\\\n2\\\n=\\\r\n\t value2\t\rkey3\\\\=value3\\\\\\\\ \r key4\:-- = val \\\r\t\t ue \\\r 4  '           
        prop.load(PropertiesTest.getInputStream(inputString))
        self.assertEqual(prop.getProperty('key1'), 'value1')
        self.assertEqual(prop.getProperty('key2'), 'value2')
        self.assertEqual(prop.getProperty('key3\\\\'), 'value3\\\\\\\\')
        self.assertEqual(prop.getProperty('key4\:--'), 'value4')
          
    def testCreatePropertyFromPropertiesFile(self):        
        inputString = 'key1\\\n= value1 \n key\\\n2\\\n=\\\r\n\t value2\t\rkey3\\\\=value3\\\\\\\\ \r key4\:-- = val \\\r\t\t ue \\\r 4  '
        f = open('tmp.properties', 'w')
        f.write(inputString)
        f.close()
        prop = p.Properties.createPropertiesFromPropertiesFile('tmp.properties')
        self.assertEqual(prop.getProperty('key1'), 'value1')
        self.assertEqual(prop.getProperty('key2'), 'value2')
        self.assertEqual(prop.getProperty('key3\\\\'), 'value3\\\\\\\\')
        self.assertEqual(prop.getProperty('key4\:--'), 'value4')
        os.remove('tmp.properties')
     
    def testCreatePropertyFromPropertiesFileExceptionFileNotFound(self):        
        self.assertTrue(PropertiesTest.__getExceptionFromCall(
            p.Properties.createPropertiesFromPropertiesFile, 'tmp.properties').__class__ == IOError)
    
    def testWritePropertiesToStream(self):
        prop = p.Properties()
        inputString = 'key1\\\n= value1 \n key\\\n2\\\n=\\\r\n\t value2\t\rkey3\\\\=value3\\\\\\\\ \r key4\:-- = val \\\r\t\t ue \\\r 4  '           
        prop.load(PropertiesTest.getInputStream(inputString))        
        prop.setProperty('key5', 'value5')
        prop.setProperty('key6', 'value6')
        outStream = PropertiesTest.getOutputStream()
        prop.store(outStream)         
        self.assertEqual(outStream.getvalue(), 'key1=value1\nkey2=value2\nkey3\\\\=value3\\\\\\\\\nkey4\:--=value4\nkey5=value5\nkey6=value6\n')
    
    def testWritePropertiesToStreamNoStream(self):
        prop = p.Properties()
        inputString = 'key1\\\n= value1 \n key\\\n2\\\n=\\\r\n\t value2\t\rkey3\\\\=value3\\\\\\\\ \r key4\:-- = val \\\r\t\t ue \\\r 4  '           
        prop.load(PropertiesTest.getInputStream(inputString))
        string_ = ''                                        
        self.assertTrue(PropertiesTest.__getExceptionFromCall(prop.store, string_, None ).__class__ == TypeError)
    
    def testWritePropertiesToStreamNotWritableStream(self):
        prop = p.Properties()
        inputString = 'key1\\\n= value1 \n key\\\n2\\\n=\\\r\n\t value2\t\rkey3\\\\=value3\\\\\\\\ \r key4\:-- = val \\\r\t\t ue \\\r 4  '           
        prop.load(PropertiesTest.getInputStream(inputString))                                                
        self.assertTrue(PropertiesTest.__getExceptionFromCall(prop.store, sys.stdin, None ).__class__ == TypeError)
    
    def testMergePropertiesSinglePropertiesListNoDefaults(self):
        prop = p.Properties()
        self.assertEqual(p.Properties.mergeProperties([prop]).properties, {})
        self.assertEqual(p.Properties.mergeProperties([prop]).defaults, None)
        prop.setProperty('key', 'value')
        self.assertEqual(p.Properties.mergeProperties([prop]).properties, prop.properties)
        self.assertEqual(p.Properties.mergeProperties([prop]).defaults, None)
    
    def testMergePropertiesSinglePropertiesListWithDefaults(self):
        prop1 = p.Properties()
        prop1.setProperty('key', 'value')
        prop = p.Properties(prop1)
        prop1.setProperty('key1', 'value1')        
        mergedProperties = p.Properties.mergeProperties([prop])
        self.assertEqual(mergedProperties.properties, dict(prop1.properties.items() + prop.properties.items()))
        self.assertEqual(mergedProperties.defaults, None)
        # with duplicate entry
        prop1 = p.Properties()
        prop1.setProperty('key', 'value')
        prop1.setProperty('key1', 'value0')
        prop = p.Properties(prop1)
        prop1.setProperty('key1', 'value1')
        mergedProperties = p.Properties.mergeProperties([prop])
        self.assertEqual(mergedProperties.properties, {'key': 'value', 'key1': 'value1'})
        self.assertEqual(mergedProperties.defaults, None)
    
    def testMergePropertiesList(self):
        prop1 = p.Properties()
        prop1.setProperty('key', 'value')
        prop1.setProperty('key1', 'value0')
        prop = p.Properties()
        prop1.setProperty('key1', 'value1')
        mergedProperties = p.Properties.mergeProperties([prop, prop1])
        self.assertEqual(mergedProperties.properties, {'key': 'value', 'key1': 'value1'})
        self.assertEqual(mergedProperties.defaults, None)
    
    def testFormattedProperty(self):
        prop = p.Properties()
        prop.setProperty('key', 'value')        
        prop.setProperty('key1', 'value1,value2,value3')
        self.assertEqual(prop.getProperty('key1', formatter = lambda s: s.split(',')), ['value1','value2','value3'])
        prop.setProperty('key2', 'value1, value2, value3')
        self.assertEqual(prop.getExpandedProperty('key2',  formatter = lambda s: map(lambda x: x.strip(), s.split(','))), ['value1','value2','value3'])
        prop.setProperty('key3', 'value2,${key2}')
        self.assertEqual(prop.getExpandedProperty('key3',  formatter = lambda s: map(lambda x: x.strip(), s.split(','))), ['value2','value1','value2','value3'])
            
    def testList(self):
        prop = p.Properties()
        out = StringIO.StringIO()
        prop.list(out=out)
        self.assertEqual(out.getvalue(), "{}\n")
        prop = p.Properties()
        prop.setProperty('key', 'value')        
        prop.setProperty('key1', 'value1,value2,value3')
        out = StringIO.StringIO()
        prop.list(out=out)
        self.assertEqual(out.getvalue(), "{'key': 'value', 'key1': 'value1,value2,value3'}\n")
        prop1 = p.Properties(prop)
        prop1.setProperty('key2', 'value2')
        out = StringIO.StringIO()
        prop1.list(out=out)
        self.assertEqual(out.getvalue(), "{'key': 'value', 'key1': 'value1,value2,value3', 'key2': 'value2'}\n")
    
    def testWrite(self):
        prop = p.Properties()
        out = StringIO.StringIO()
        prop.store(out=out)
        self.assertEqual(out.getvalue(), '')
        prop = p.Properties()
        prop.setProperty('key', 'value')
        prop.setProperty('key1', 'value1,value2,value3')
        out = StringIO.StringIO()
        prop.store(out=out)
        self.assertEqual(out.getvalue(), 'key=value\nkey1=value1,value2,value3\n')
        prop1 = p.Properties(prop)
        prop1.setProperty('key2', 'value2')
        prop1.setProperty('key1', 'value1')
        out = StringIO.StringIO()
        prop1.store(out=out)
        self.assertEqual(out.getvalue(), 'key1=value1\nkey2=value2\n')
    
if __name__ == "__main__":    
    unittest.main()