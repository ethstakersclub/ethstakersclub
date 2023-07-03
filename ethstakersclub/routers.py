class UserdataRouter:
    app_labels = ['users', 'admin', 'auth', 'contenttypes', 'sessions', 'allauth', 'account', 'socialaccount', 'sites', 'captcha']

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.app_labels:
            return 'userdata'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.app_labels:
            return 'userdata'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.app_labels or
            obj2._meta.app_label in self.app_labels
        ):
            return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.app_labels:
            return db == 'userdata'
        elif db == 'userdata':
            print(app_label)
            return False
        return None