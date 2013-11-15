import logging
import os
import random
import re


class PluginSelector(object):
    
    @classmethod
    def get_all(cls):
        return cls.get_plugin_classes()
    
    @classmethod
    def get_plugin_classes(cls):
        return Plugin.__subclasses__()
    
    def __init__(self, options):
        self.options = options
        
    def get_plugin_class_for(self, string):
        plugin_classes = self.get_plugin_classes()
        candidates = filter(lambda cls: cls.__name__ == string, plugin_classes)
        if not candidates:
            raise Exception('plugin %s not found!' % string)
        return candidates[0]
    
    def value(self):
        plugin_string = self.options.plugins.split(',')
        plugin_classes = map(lambda plugin:
                                self.get_plugin_class_for(plugin.strip()),
                             plugin_string)
        plugins = map(lambda plugin_class: plugin_class(self.options),
                      plugin_classes)
        return plugins


class Plugin(object):
    
    @classmethod
    def name(cls):
        raise NotImplementedError('Subclasses should implement this method')
    
    def can_handle(self, request):
        raise NotImplementedError('Subclasses should implement this method')
    
    def value(self, data):
        logging.log(logging.INFO, 'Applying %s plugin' % self.name())
        return self.apply_to(data)
        
    def apply_to(self, data):
        raise NotImplementedError('Subclasses should implement this method')    


class ImageExchangerPlugin(Plugin):
    
    @classmethod
    def name(cls):
        return 'Image Exchanger'    

    def __init__(self, options):
        self.image_directory = options.image_directory
        self.exchange_probability = options.image_exchange_probability
        self.initialize_images()
        
    def initialize_images(self):
        self.images = list()
        files = os.listdir(self.image_directory)
        for filename in files:
            img = open('%s/%s' % (self.image_directory, filename), 'r').read()
            self.images.append(img)
        
    def can_handle(self, request):
        content_type = request.headers_received.get('Content-Type', str())
        return 'image/jpeg' in content_type or 'image/jpg' in content_type    

    def get_similar_to(self, size):
        most_similar = self.images[0]
        most_similar_diff = abs(size - len(most_similar))
        for img in self.images[1:]:
            img_len = len(img)
            diff = abs(size - img_len)
            if diff < most_similar_diff:
                most_similar = img
                most_similar_diff = diff
        return most_similar
    
    def apply_to(self, data):
        should_change = random.random() < self.exchange_probability
        image = data
        if should_change:
            image = self.get_similar_to(len(image))
        return image

    
class StringExchangerPlugin(Plugin):

    @classmethod
    def name(cls):
        return 'String Exchanger'

    def __init__(self, options):
        self.mappings_file = options.mappings_file
        self.initialize_strings()
        
    def initialize_strings(self):
        mappings = open(self.mappings_file, 'r').readlines()
        self.strings = dict()
        for line in mappings:
            word, mapping = line.split('\t')
            self.strings[word.strip()] = mapping.strip()

    def can_handle(self, request):
        content_type = request.headers_received.get('Content-Type', str())
        return 'text/html' in content_type

    def replace(self, data, word, mapping):
        word_regexp = re.compile(word, re.IGNORECASE)
        new_data = word_regexp.sub(mapping, data)
        return new_data
    
    def apply_to(self, data):
        for word, mapping in self.strings.items():
            data = self.replace(data, word, mapping)
        return data