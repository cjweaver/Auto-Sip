
Auto SIP user manual v.1

  
  

**Auto SIP user manual**

*This document is intended to describe the function of the Auto-SIP script. To use this script, you should have a thorough understanding of how to build p-SIPs from the beginning to the Process Metadata stage. SIP tool training is available from Preservation Audio Engineers at the British Library and UOSH partner institutions.*

  

The Auto SIP script automates Chrome and the AV SIP tool. The script is run in the same directory as the accompanying SIPS.xls spreadsheet as it refers back to data inputted in these cells. If the SIPS.xls spreadsheet is unavailable, the script will not run. The Auto SIP relies on a reference SIP to be created. The reference SIP number can be found in that SIP’s URL (add URL example here).

  

SIPS.xls Cells

  

It's easiest to think of the cells in the SIPS.xls as representing the different data you would input when creating a pSIP manually.

  

In this example, we'll use shelf mark C123/123 which is a group comprising of C123/123-126

  
  

1. Shelf Mark

This cell refers to the shelf mark which is linked in the British Library's Sound and Moving Image (SAMI) catalogue recording entry by an MDArk. This can be found on the first page of the SIP tool.

  

We'll use a group in this example: C123/123-126. Because of the way SAMI entries are grouped, typing C123/123 will link to the group C123/123-126.

  

2. File Name

  

This cell is used to enter the filename(s) to be associated with the recording entry specified by the shelf mark in step 1. You can add as many files as required by separating them with a semicolon (no space).

  

eg. C123_123;C123_124;C123/125;C123_126

  

3. Old BL Filename

  

This cell refers to the previous filename structure used at the British Library. To be used by BL staff when uploading surrogate files.

  
  

4. Directory

  

Input the directory of the file(s) location you wish to upload to the p-SIP.

  

5. Item Format

  

The audio format is defined in this cell. This step will specify the format in the Physical Structure of the p-SIP. The options are: Cylinder, Disc, Sheet, Solid State, Tape

  

6. Date

  

The date entered here will define the date for the Process Metadata page. The options are:

  

YES: uses the date the file was created

NO: uses the date in the reference SIP

DD/MM/YYYY: enter a date

  

7. Reference SIP

  

Add the reference SIP number which can be found in the URL for the SIP you are replicating.

  

8. Speed

  

This cell defines the speed of the carrier in the Process Metadata page. The drop down menu has the available speeds. Auto SIP will use the speed settings in the reference SIP if this is left blank.

  

9. EQ

  

This cell specifies any equalisation used in the Process Metadata. A drop down menu has the available EQ types. Auto SIP will use the EQ settings in the reference SIP if this is left blank.
enter link description here
  

10. Noise Reduction

  

This cell specifies any noise reduction used in the Process Metadata. A drop down menu has the available noise reduction types. Auto SIP will use the noise reduction settings in the reference SIP if this is left blank.

  

11. Notes

  

This cell will enter any free text in the notes field in the Process Metadata page.

