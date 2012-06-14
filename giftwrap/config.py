from grabbag.property import cached_property
from grabbag.dict import merge


# a class that allows setting of request attrs with uber-flexibility (via any combo of class variable, instance method, constructor parameter, or fallback config)

class _Config(object):
    ATTRS = ('method','protocol','domain','base_path','sub_path','params','headers','data','timeout','max_retries')
    ADDITIVE_ATTRS = set(('headers','params'))
    TRUTHY_ATTRS = set(('method', 'protocol', 'domain', 'base_path', 'sub_path'))

    @classmethod  # creates properties and works around nameclashing pitfalls
    def _build_attr_properties(kls):
        if kls.__dict__.get('_built'): return 
        for attr in kls.ATTRS:
            def _tmp(self, attr, klass_value, cleanup_method):
                if hasattr(klass_value, '__call__'):
                    klass_value = klass_value(self)
                instance_value = self._init_kwargs.get(attr,None)
                val = None
                if attr in kls.ADDITIVE_ATTRS:
                    val = merge({}, getattr(self.fallthrough,attr,{}), klass_value, instance_value)
                elif attr in kls.TRUTHY_ATTRS:
                    val = instance_value or klass_value or getattr(self.fallthrough,attr,None)
                else:
                    if instance_value is not None: val=instance_value
                    elif klass_value is not None: val=klass_value
                    else: val = getattr(self.fallthrough,attr,None)
                return cleanup_method(val)
            klass_value = getattr(kls,attr,None)
            #if hasattr(klass_value, '__call__'):
                #klass_value = setattr(kls, '__exchange_%s'%attr, klass_value)
            cleanup_method = getattr(kls,'ATTR_CLEANUPS',{}).get(attr,lambda x:x)
            setattr(kls,attr,cached_property(_tmp,attr,attr,klass_value,cleanup_method))
        kls._built=True

    def __init__(self, *args, **kwargs):
        super(_Config, self).__init__()
        self._init_kwargs = kwargs


class Config(_Config):
    def __init__(self, fallthrough=None, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.fallthrough = fallthrough or DefaultConfig()
        self.__class__._build_attr_properties()


class DefaultConfig(_Config):
    method = 'GET'
    protocol = 'https'
    timeout = 20
    max_retries = 0


