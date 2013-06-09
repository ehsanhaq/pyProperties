# pyProperties

Java like Properties implementation in Python. It aims to provide a `java.util.Properties` like functionality.

The Properties class represents a persistent set of properties. The Properties can be saved to a stream or loaded from a stream. Each key and its corresponding value in the property list is a string.

A property list can contain another property list as its "defaults"; this second property list is searched if the property key is not found in the original property list.

#### Highlights
* Default Properties.
* Referencing Properties in other properties e.g. key=${ref-key}
* Storing and Retreving Properties from stream and file.
* Supports .properties file format [http://docs.oracle.com/javase/6/docs/api/java/util/Properties.html](http://docs.oracle.com/javase/6/docs/api/java/util/Properties.html)
* Merge several properties.

#### TODO
* Namespace filtering.
* XML based properties.