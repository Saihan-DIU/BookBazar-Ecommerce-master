from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import Address, UserProfile, Book, Category
from django.template.defaultfilters import slugify

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    shipping_zip_code = forms.CharField(required=False)

    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    billing_zip_code = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        same_billing_address = cleaned_data.get('same_billing_address')
        use_default_shipping = cleaned_data.get('use_default_shipping')
        use_default_billing = cleaned_data.get('use_default_billing')

        # Validate shipping address
        if not use_default_shipping:
            shipping_address = cleaned_data.get('shipping_address')
            shipping_country = cleaned_data.get('shipping_country')
            shipping_zip_code = cleaned_data.get('shipping_zip_code')
            
            if not shipping_address:
                self.add_error('shipping_address', 'This field is required')
            if not shipping_country:
                self.add_error('shipping_country', 'This field is required')
            if not shipping_zip_code:
                self.add_error('shipping_zip_code', 'This field is required')

        # Validate billing address
        if not same_billing_address and not use_default_billing:
            billing_address = cleaned_data.get('billing_address')
            billing_country = cleaned_data.get('billing_country')
            billing_zip_code = cleaned_data.get('billing_zip_code')
            
            if not billing_address:
                self.add_error('billing_address', 'This field is required')
            if not billing_country:
                self.add_error('billing_country', 'This field is required')
            if not billing_zip_code:
                self.add_error('billing_zip_code', 'This field is required')

        return cleaned_data


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and len(code) < 4:
            raise forms.ValidationError("Promo code must be at least 4 characters long.")
        return code


class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        stripeToken = cleaned_data.get('stripeToken')
        use_default = cleaned_data.get('use_default')

        if not use_default and not stripeToken:
            raise forms.ValidationError("Please provide a payment method or use your default card.")

        return cleaned_data


class ContactForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name'
        })
    )
    subject = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject of your message'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your message...',
            'rows': 5
        }),
        required=True
    )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name.strip()

    def clean_subject(self):
        subject = self.cleaned_data.get('subject')
        if len(subject.strip()) < 5:
            raise forms.ValidationError("Subject must be at least 5 characters long.")
        return subject.strip()

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message.strip()) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        return message.strip()

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            'street_address', 
            'apartment_address', 
            'country', 
            'zip_code',
            'address_type', 
            'default'
        )
        widgets = {
            'street_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234 Main St'
            }),
            'apartment_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment or suite'
            }),
            'country': CountrySelectWidget(attrs={
                'class': 'custom-select d-block w-100'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Zip code'
            }),
            'address_type': forms.Select(attrs={
                'class': 'custom-select d-block w-100'
            }),
        }

    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code')
        if zip_code and len(zip_code) < 3:
            raise forms.ValidationError("Zip code must be at least 3 characters long.")
        return zip_code

    def clean_street_address(self):
        street_address = self.cleaned_data.get('street_address')
        if not street_address:
            raise forms.ValidationError("Street address is required.")
        if len(street_address.strip()) < 5:
            raise forms.ValidationError("Street address must be at least 5 characters long.")
        return street_address.strip()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['one_click_purchasing']
        widgets = {
            'one_click_purchasing': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'additional_authors',
            'isbn',
            'isbn13',
            'category',
            'genre',
            'format_type',
            'condition',
            'publisher',
            'publication_date',
            'edition',
            'pages',
            'language',
            'price',
            'discount_price',
            'label1',
            'label2',
            'label3',
            'cover_image',
            'additional_images',
            'description',
            'excerpt',
            'stock_quantity',
            'is_available',
            'slug'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title'
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter primary author name'
            }),
            'additional_authors': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter additional authors (comma separated)'
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ISBN (10 digits)'
            }),
            'isbn13': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ISBN-13 (13 digits)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'genre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter genre'
            }),
            'format_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'condition': forms.Select(attrs={
                'class': 'form-control'
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter publisher name'
            }),
            'publication_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'edition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter edition (e.g., First Edition)'
            }),
            'pages': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of pages',
                'min': '1'
            }),
            'language': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter language'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'label1': forms.Select(attrs={
                'class': 'form-control'
            }),
            'label2': forms.Select(attrs={
                'class': 'form-control'
            }),
            'label3': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
            'additional_images': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter book description...'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter book excerpt...'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter stock quantity',
                'min': '0'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug'
            }),
        }
        labels = {
            'cover_image': 'Book Cover Image',
            'additional_images': 'Additional Images',
            'is_available': 'Available for purchase',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make essential fields required
        self.fields['title'].required = True
        self.fields['author'].required = True
        self.fields['category'].required = True
        self.fields['price'].required = True
        
        # Add empty choice for label fields
        for field in ['label1', 'label2', 'label3']:
            self.fields[field].empty_label = "Select label"
        
        # Style the image fields
        self.fields['cover_image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })
        self.fields['additional_images'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("Title is required.")
        if len(title.strip()) < 2:
            raise forms.ValidationError("Title must be at least 2 characters long.")
        return title.strip()

    def clean_author(self):
        author = self.cleaned_data.get('author')
        if not author:
            raise forms.ValidationError("Author is required.")
        if len(author.strip()) < 2:
            raise forms.ValidationError("Author name must be at least 2 characters long.")
        return author.strip()

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if isbn and len(isbn.strip()) not in [10, 13]:
            raise forms.ValidationError("ISBN must be 10 or 13 digits long.")
        return isbn.strip() if isbn else isbn

    def clean_isbn13(self):
        isbn13 = self.cleaned_data.get('isbn13')
        if isbn13 and len(isbn13.strip()) != 13:
            raise forms.ValidationError("ISBN-13 must be exactly 13 digits long.")
        return isbn13.strip() if isbn13 else isbn13

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        return price

    def clean_discount_price(self):
        discount_price = self.cleaned_data.get('discount_price')
        price = self.cleaned_data.get('price')
        
        if discount_price:
            if discount_price <= 0:
                raise forms.ValidationError("Discount price must be greater than 0.")
            if price and discount_price >= price:
                raise forms.ValidationError("Discount price must be less than regular price.")
        
        return discount_price

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity is None or stock_quantity < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return stock_quantity

    def clean_pages(self):
        pages = self.cleaned_data.get('pages')
        if pages and pages <= 0:
            raise forms.ValidationError("Number of pages must be greater than 0.")
        return pages

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("Description is required.")
        if len(description.strip()) < 10:
            raise forms.ValidationError("Description must be at least 10 characters long.")
        return description.strip()

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Generate slug from title if slug field exists and is empty
        if instance.title and not instance.slug:
            base_slug = slugify(instance.title)
            slug = base_slug
            counter = 1
            
            # Ensure slug is unique
            while Book.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            instance.slug = slug
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category description',
                'rows': 3
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Category name is required.")
        if len(name.strip()) < 2:
            raise forms.ValidationError("Category name must be at least 2 characters long.")
        return name.strip()

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Generate slug from name
        if instance.name:
            base_slug = slugify(instance.name)
            slug = base_slug
            counter = 1
            
            # Ensure slug is unique
            while Category.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            instance.slug = slug
        
        if commit:
            instance.save()
        
        return instance


class ProductSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search books...',
            'aria-label': 'Search'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min price',
            'step': '0.01'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max price',
            'step': '0.01'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price.")
        
        return cleaned_data


class ReviewForm(forms.Form):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Share your thoughts about this book...'
        }),
        required=False
    )

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating:
            raise forms.ValidationError("Please select a rating.")
        return int(rating)