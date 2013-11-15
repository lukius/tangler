import logging
import sys
from argparse import ArgumentParser

from proxy import TanglerProxy
from plugins import PluginSelector


def parse_options():
    parser = ArgumentParser()
    
    parser.add_argument("-P", "--plugins", dest="plugins", action="store",
                        default=','.join([plugin.__name__ for plugin in PluginSelector.get_all()]),
                        type=str,
                        help="list of comma-separated plugins to use (defaults to everyone available) ")
    
    parser.add_argument("-p", "--port", dest="port", action="store",
                        default=8080, type=int,
                        help="port where the proxy will be listening (defaults to 8080) ")
    
    parser.add_argument("-t", "--timeout", dest="timeout", action="store",
                        default=100, help="connection timeout ", type=int)
    
    parser.add_argument("-m", "--mappings", action="store", dest="mappings_file",
                        default="./samples/mappings.txt", type=str,
                        help = "path to local file containing word mappings to use on the string exchanger plugin ")
    
    parser.add_argument("-i", "--images", action="store", dest="image_directory",
                        default="./samples/images", type=str,
                        help="path to local directory containing JPG images to use on the image exchanger plugin ")
    
    parser.add_argument("-r", "--image-exchange-probability", action="store", dest="image_exchange_probability",
                        default=0.5, type=float,
                        help="value between 0 and 1 indicating how likely is for an image to be replaced (used on image replacer plugin) ")
    
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                        help="use this option to make Tangler log everything that is going around ")        
    
    options = parser.parse_args()

    if options.image_exchange_probability < 0 or\
       options.image_exchange_probability > 1:
        print 'image exchange probability should be between 0 and 1!'
        sys.exit()
    
    logging_level = logging.DEBUG if options.verbose else logging.CRITICAL    
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    options.plugins = PluginSelector(options).value()
        
    return options

def main():
    options = parse_options()
    TanglerProxy(options).run()    


if __name__ == '__main__':
    main()