# -*- coding: utf-8 -*-

from datetime import *
from django.db import models
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from koalixcrm.plugin import *
from koalixcrm.crm.contact.phoneaddress import PhoneAddress
from koalixcrm.crm.contact.emailaddress import EmailAddress
from koalixcrm.crm.contact.postaladdress import PostalAddress
from koalixcrm.crm.documents.invoice import Invoice
from koalixcrm.crm.documents.quote import Quote
from koalixcrm.crm.documents.purchaseorder import PurchaseOrder
from koalixcrm.globalSupportFunctions import xstr
from koalixcrm.crm.const.purpose import *
from koalixcrm.crm.documents.invoice import InlineInvoice
from koalixcrm.crm.documents.quote import InlineQuote
from koalixcrm.crm.exceptions import *


class PostalAddressForContract(PostalAddress):
    purpose = models.CharField(verbose_name=_("Purpose"), max_length=1, choices=PURPOSESADDRESSINCONTRACT)
    contract = models.ForeignKey('Contract')

    class Meta:
        app_label = "crm"
        verbose_name = _('Postal Address For Contracts')
        verbose_name_plural = _('Postal Address For Contracts')

    def __str__(self):
        return xstr(self.prename) + ' ' + xstr(self.name) + ' ' + xstr(self.addressline1)


class PhoneAddressForContract(PhoneAddress):
    purpose = models.CharField(verbose_name=_("Purpose"), max_length=1, choices=PURPOSESADDRESSINCONTRACT)
    contract = models.ForeignKey('Contract')

    class Meta:
        app_label = "crm"
        verbose_name = _('Phone Address For Contracts')
        verbose_name_plural = _('Phone Address For Contracts')

    def __str__(self):
        return str(self.phone)


class EmailAddressForContract(EmailAddress):
    purpose = models.CharField(verbose_name=_("Purpose"), max_length=1, choices=PURPOSESADDRESSINCONTRACT)
    contract = models.ForeignKey('Contract')

    class Meta:
        app_label = "crm"
        verbose_name = _('Email Address For Contracts')
        verbose_name_plural = _('Email Address For Contracts')

    def __str__(self):
        return str(self.email)


class ContractPostalAddress(admin.StackedInline):
    model = PostalAddressForContract
    extra = 1
    classes = ['collapse']
    fieldsets = (
        ('Basics', {
            'fields': (
            'prefix', 'prename', 'name', 'addressline1', 'addressline2', 'addressline3', 'addressline4', 'zipcode',
            'town', 'state', 'country', 'purpose'),
        }),
    )
    allow_add = True


class ContractPhoneAddress(admin.TabularInline):
    model = PhoneAddressForContract
    extra = 1
    classes = ['collapse']
    fieldsets = (
        ('Basics', {
            'fields': ('phone', 'purpose',)
        }),
    )
    allow_add = True


class ContractEmailAddress(admin.TabularInline):
    model = EmailAddressForContract
    extra = 1
    classes = ['collapse']
    fieldsets = (
        ('Basics', {
            'fields': ('email', 'purpose',)
        }),
    )
    allow_add = True


class Contract(models.Model):
    staff = models.ForeignKey('auth.User', limit_choices_to={'is_staff': True}, blank=True, verbose_name=_("Staff"),
                              related_name="db_relcontractstaff", null=True)
    description = models.TextField(verbose_name=_("Description"))
    default_customer = models.ForeignKey("Customer", verbose_name=_("Default Customer"), null=True, blank=True)
    default_supplier = models.ForeignKey("Supplier", verbose_name=_("Default Supplier"), null=True, blank=True)
    default_currency = models.ForeignKey("Currency", verbose_name=_("Default Currency"), blank=False, null=False)
    default_template_set = models.ForeignKey("djangoUserExtension.TemplateSet", verbose_name=_("Default Template Set"), null=True, blank=True)
    date_of_creation = models.DateTimeField(verbose_name=_("Created at"), auto_now_add=True)
    last_modification = models.DateTimeField(verbose_name=_("Last modified"), auto_now=True)
    last_modified_by = models.ForeignKey('auth.User', limit_choices_to={'is_staff': True},
                                         verbose_name=_("Last modified by"), related_name="db_contractlstmodified")

    class Meta:
        app_label = "crm"
        verbose_name = _('Contract')
        verbose_name_plural = _('Contracts')

    def get_template_set(self, calling_model):
        if self.default_template_set:
            required_template_set = str(type(calling_model).__name__)
            return self.default_template_set.get_template_set(required_template_set)
        else:
            raise TemplateSetMissing("The Contract has no Default Template Set selected")

    def create_invoice(self):
        invoice = Invoice()
        invoice.create_invoice(self)
        return invoice

    def create_quote(self):
        quote = Quote()
        quote.create_quote(self)
        return quote

    def create_purchase_order(self):
        purchase_order = PurchaseOrder()
        purchase_order.create_purchase_order(self)
        return purchase_order

    def __str__(self):
        return _("Contract") + " " + str(self.id)


class OptionContract(admin.ModelAdmin):
    list_display = ('id', 'description', 'default_customer', 'default_supplier', 'staff', 'default_currency')
    list_display_links = ('id',)
    list_filter = ('default_customer', 'default_supplier', 'staff', 'default_currency')
    ordering = ('id', )
    search_fields = ('id', 'contract')
    fieldsets = (
        (_('Basics'), {
            'fields': ('description', 'default_customer', 'staff', 'default_supplier', 'default_currency', 'default_template_set')
        }),
    )
    inlines = [ContractPostalAddress, ContractPhoneAddress, ContractEmailAddress, InlineQuote, InlineInvoice]
    pluginProcessor = PluginProcessor()
    inlines.extend(pluginProcessor.getPluginAdditions("contractInlines"))

    def create_purchase_order(self, request, queryset):
        for obj in queryset:
            purchase_order = obj.create_purchase_order()
            self.message_user(request, _("PurchaseOrder created"))
            response = HttpResponseRedirect('/admin/crm/purchaseorder/' + str(purchase_order.id))
        return response

        create_purchase_order.short_description = _("Create Purchaseorder")

    def create_quote(self, request, queryset):
        for obj in queryset:
            quote = obj.create_quote()
            self.message_user(request, _("Quote created"))
            response = HttpResponseRedirect('/admin/crm/quote/' + str(quote.id))
        return response

    create_quote.short_description = _("Create Quote")

    def create_invoice(self, request, queryset):
        for obj in queryset:
            invoice = obj.create_invoice()
            self.message_user(request, _("Invoice created"))
            response = HttpResponseRedirect('/admin/crm/invoice/' + str(invoice.id))
        return response

    create_invoice.short_description = _("Create Invoice")

    def create_delivery_note(self, request, queryset):
        for obj in queryset:
            delivery_note = obj.create_delivery_note()
            self.message_user(request, _("Delivery Note created"))
            response = HttpResponseRedirect('/admin/crm/deliverynote/' + str(delivery_note.id))
        return response

    create_delivery_note.short_description = _("Create Delivery Note")

    def create_payment_reminder(self, request, queryset):
        for obj in queryset:
            payment_reminder = obj.create_delivery_note()
            self.message_user(request, _("Payment Reminder created"))
            response = HttpResponseRedirect('/admin/crm/paymentreminder/' + str(payment_reminder.id))
        return response

    create_payment_reminder.short_description = _("Create Payment Reminder")

    def save_model(self, request, obj, form, change):
        if (change == True):
            obj.last_modified_by = request.user
        else:
            obj.last_modified_by = request.user
            obj.staff = request.user
        obj.save()

    actions = ['create_quote', 'create_invoice', 'create_purchase_order']
    pluginProcessor = PluginProcessor()
    actions.extend(pluginProcessor.getPluginAdditions("contractActions"))

