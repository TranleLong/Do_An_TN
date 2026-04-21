import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_tien_huong.settings')
django.setup()

from apps.ban_hang.models import HoaDonBan
from apps.so_cai.models import JournalEntry, JournalEntryLine

# Check Invoices
invoices = HoaDonBan.objects.all()
print(f"Total Invoices: {invoices.count()}")
for hd in invoices:
    print(f"HD: {hd.so_hoa_don}, Status: {hd.trang_thai}, Date: {hd.ngay_lap}, Posted Date: {hd.ngay_hach_toan}")

# Check Journal Entries
jes = JournalEntry.objects.all()
print(f"Total Journal Entries: {jes.count()}")
for je in jes:
    print(f"JE: {je.entry_number}, Type: {je.document_type}, DocNum: {je.document_number}, Date: {je.posting_date}")
    for line in je.lines.all():
        print(f"  Line: {line.account.ma_tk}, Debit: {line.debit_amount}, Credit: {line.credit_amount}")

# Check specific HDX00001
hd = HoaDonBan.objects.filter(so_hoa_don__icontains='HDX00001').first()
if hd:
    print(f"\nTarget HD: {hd.so_hoa_don}, ID: {hd.id}, Status: {hd.trang_thai}")
    je = JournalEntry.objects.filter(document_type='hoa_don_ban', document_id=hd.id).first()
    if je:
        print(f"Linked JE: {je.entry_number}, Status: {je.status}")
    else:
        print("No linked JE found for this invoice ID.")
else:
     print("\nTarget HDX00001 not found.")
