# OCR ON/OFF Folder Parsing Report

- Generated at: 2026-04-21T06:00:09Z
- Input directory: benchmark_samples
- Supported extensions: bmp, csv, doc, docm, docx, htm, html, jpeg, jpg, json, md, pdf, png, pptx, rtf, tif, tiff, tsv, txt, webp, xls, xlsb, xlsm, xlsx, xml
- Total files: 11
- Files with errors: 0
- Files with warnings: 0
- Files with dependency/toolchain issues: 0
- OCR ON parsed with ocr_used=True: 1
- Files with table marker improvement (ON > OFF): 1

## Priority Findings

No critical findings detected. Residual risk remains for files without explicit table markers but with weak tabular hints.

## Table Quality Overview

- Table check pass: 6
- Table check warn: 0
- Table check fail: 0
- Table check blocked: 0
- Table check n/a: 5

## File Summary

| File | Ext | Severity | Table Check | OCR Used | Chars ON | Chars OFF | Table Gain |
|---|---|---|---|---:|---:|---:|---:|
| benchmark_samples/attention_is_all_you_need.pdf | pdf | ok | pass | yes | 97912 | 58915 | 3 |
| benchmark_samples/docx_template.docx | docx | ok | n/a | no | 453 | 453 | 0 |
| benchmark_samples/pandas_test1.xls | xls | ok | pass | no | 1729 | 1729 | 0 |
| benchmark_samples/pandas_test1.xlsb | xlsb | ok | pass | no | 1533 | 1533 | 0 |
| benchmark_samples/pandas_test1.xlsx | xlsx | ok | pass | no | 1729 | 1729 | 0 |
| benchmark_samples/real_spec.html | html | ok | pass | no | 256832 | 256832 | 0 |
| benchmark_samples/repo_sample.doc | doc | ok | n/a | no | 765 | 765 | 0 |
| benchmark_samples/repo_sample.pptx | pptx | ok | n/a | no | 808 | 808 | 0 |
| benchmark_samples/sample_data.csv | csv | ok | pass | no | 3047 | 3047 | 0 |
| benchmark_samples/sample_data.json | json | ok | n/a | no | 85332 | 85332 | 0 |
| benchmark_samples/sample_xml.xml | xml | ok | n/a | no | 122 | 122 | 0 |

## Per-file Details

### benchmark_samples/attention_is_all_you_need.pdf

- Extension: pdf
- Size bytes: 2215244
- Quality severity: ok
- Chars gain (ON - OFF): 38997
- Table gain (ON - OFF): 3
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: pass
- Table check reason: Table hints and table marker detected.

OCR ON preview:

```text
‡Work performed while at Google Research.
31st Conference on Neural Information Processing Systems (NIPS 2017), Long Beach, CA, USA.
[TABLE_START]
| | Providedproperattributionisprovided,Googleherebygrantspermissionto |
| --- | --- |
[10], consuming the previously generated symbols as additional input when generating the next.
2
[TABLE_START]
| 1 Introduction |
| --- |
An attention function can be described as mapping a query and a set of key-value pairs to an output,
where the query, keys, values, and output are all vectors. The output is computed as a weighted sum
[TABLE_START]
| TheTransformerfollowsthisoverallarchitectureusingstackedself-attentionandpoint-wise,fully |
| --- |
4To illustrate why the dot products get large, assume that the components of q and k are independent random
yn
[TABLE_START]
| SoftMax MatMul | Concat Linear |
| Mask (opt.) Scale | Scaled Dot-Product Attention |
| 3.2.2Multi-HeadAttention | Instead of performing a single attention function with dmodel-dimensional keys, values and queries, we found it beneficial to linearly project the queries, keys and values h times with different, learned linear projections to dk, dk and d, dimensions, respectively. On each of these projected versions of queries,keys and values we then perform the attention function in parallel, yielding d-dimensional 4To illustrate why the dot products get large, assume that the components of q and k are independent random yn |
[TABLE_END]
```

OCR OFF preview:

```text
‡Work performed while at Google Research.
31st Conference on Neural Information Processing Systems (NIPS 2017), Long Beach, CA, USA.
[TABLE_START]
| | Providedproperattributionisprovided,Googleherebygrantspermissionto |
| --- | --- |
## Page 2
2
[TABLE_START]
| 1 Introduction |
| --- |
Figure 1: The Transformer - model architecture.
3
[TABLE_START]
| TheTransformerfollowsthisoverallarchitectureusingstackedself-attentionandpoint-wise,fully |
| --- |
Scaled Dot-Product Attention Multi-Head Attention
4
[TABLE_START]
| Figure 2: (left) Scaled Dot-Product Attention. (right) Multi-Head Attention consists of several |
| --- |
## Page 5
5
```

### benchmark_samples/docx_template.docx

- Extension: docx
- Size bytes: 14052
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: n/a
- Table check reason: No strong table expectation for this file type.

OCR ON preview:

```text
Inline image : {{ myimage }} -> you can write just after
Image with a forced ratio : {{ myimageratio }}
# In a table :
[TABLE_START]
| Image | Description |
| --- | --- |
```

OCR OFF preview:

```text
Inline image : {{ myimage }} -> you can write just after
Image with a forced ratio : {{ myimageratio }}
# In a table :
[TABLE_START]
| Image | Description |
| --- | --- |
```

### benchmark_samples/pandas_test1.xls

- Extension: xls
- Size bytes: 28672
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: pass
- Table check reason: Expected [TABLE_START] marker found for tabular input.

OCR ON preview:

```text
## Sheet: Sheet1
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| 2000-01-03 00:00:00 | 0.980268513777 | 3.68573087906 | -0.364216805298 | -1.15973806169 |
[TABLE_END]
## Sheet: Sheet2
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| | col | we | should | ignore |
[TABLE_END]
## Sheet: Sheet3
[TABLE_START]
| A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- |
[TABLE_END]
## Sheet: Sheet4
[TABLE_START]
| i1 | a | x |
| --- | --- | --- |
```

OCR OFF preview:

```text
## Sheet: Sheet1
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| 2000-01-03 00:00:00 | 0.980268513777 | 3.68573087906 | -0.364216805298 | -1.15973806169 |
[TABLE_END]
## Sheet: Sheet2
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| | col | we | should | ignore |
[TABLE_END]
## Sheet: Sheet3
[TABLE_START]
| A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- |
[TABLE_END]
## Sheet: Sheet4
[TABLE_START]
| i1 | a | x |
| --- | --- | --- |
```

### benchmark_samples/pandas_test1.xlsb

- Extension: xlsb
- Size bytes: 11359
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: pass
- Table check reason: Expected [TABLE_START] marker found for tabular input.

OCR ON preview:

```text
## Sheet: Sheet1
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| 36528 | 0.980268513777 | 3.68573087906 | -0.364216805298 | -1.15973806169 |
[TABLE_END]
## Sheet: Sheet2
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| | col | we | should | ignore |
[TABLE_END]
## Sheet: Sheet3
[TABLE_START]
| A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- |
[TABLE_END]
## Sheet: Sheet4
[TABLE_START]
| i1 | a | x |
| --- | --- | --- |
```

OCR OFF preview:

```text
## Sheet: Sheet1
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| 36528 | 0.980268513777 | 3.68573087906 | -0.364216805298 | -1.15973806169 |
[TABLE_END]
## Sheet: Sheet2
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| | col | we | should | ignore |
[TABLE_END]
## Sheet: Sheet3
[TABLE_START]
| A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- |
[TABLE_END]
## Sheet: Sheet4
[TABLE_START]
| i1 | a | x |
| --- | --- | --- |
```

### benchmark_samples/pandas_test1.xlsx

- Extension: xlsx
- Size bytes: 12074
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: pass
- Table check reason: Expected [TABLE_START] marker found for tabular input.

OCR ON preview:

```text
## Sheet: Sheet1
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| 2000-01-03 00:00:00 | 0.980268513777 | 3.68573087906 | -0.364216805298 | -1.15973806169 |
[TABLE_END]
## Sheet: Sheet2
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| | col | we | should | ignore |
[TABLE_END]
## Sheet: Sheet3
[TABLE_START]
| A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- |
[TABLE_END]
## Sheet: Sheet4
[TABLE_START]
| i1 | a | x |
| --- | --- | --- |
```

OCR OFF preview:

```text
## Sheet: Sheet1
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| 2000-01-03 00:00:00 | 0.980268513777 | 3.68573087906 | -0.364216805298 | -1.15973806169 |
[TABLE_END]
## Sheet: Sheet2
[TABLE_START]
| Column 1 | A | B | C | D |
| --- | --- | --- | --- | --- |
| | col | we | should | ignore |
[TABLE_END]
## Sheet: Sheet3
[TABLE_START]
| A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- |
[TABLE_END]
## Sheet: Sheet4
[TABLE_START]
| i1 | a | x |
| --- | --- | --- |
```

### benchmark_samples/real_spec.html

- Extension: html
- Size bytes: 656574
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: pass
- Table check reason: Table hints and table marker detected.

OCR ON preview:

```text
the group; that page also includes
instructions for disclosing a patent. An individual who has actual
knowledge of a patent which the individual believes contains Essential Claim(s) must disclose the information in accordance with section 6 of the W3C Patent Policy . This document is governed by the 03 November 2023 W3C Process Document . Table of Contents Abstract Status of This Document 1. Introduction 2. Scope 3. Terms, definitions, and abbreviated terms 4. Concepts 4.1 Static and Animated images 4.2 Images 4.3 Color spaces 4.4 Reference image to PNG image transformation Introduction 4.4.1 Alpha separation 4.4.2 Indexing 4.4.3 RGB merging 4.4.4 Alpha compaction 4.4.5 Sample depth scaling 4.5 PNG image 4.6 Encoding the PNG image Introduction 4.6.1 Pass extraction 4.6.2 Scanline serialization 4.6.3 Filtering 4.6.4 Compression 4.6.5 Chunking 4.7 Additional information 4.8 PNG datastream 4.8.1 Chunks 4.8.2 Chunk types 4.9 APNG : frame-based animation Introduction 4.9.1 Structure 4.9.2 Sequence numbers 4.9.3 Output buffer 4.9.4 Canvas 4.10 Error handling 4.11 Extensions 5. Datastream structure 5.1 PNG datastream 5.2 PNG signature 5.3 Chunk layout 5.4 Chunk naming conventions 5.5 CRC algorithm 5.6 Chunk ordering 5.7 Defining chunks 5.7.1 General 5.7.2 Defining public chunks 5.7.3 Defining private chunks 5.8 Private field values 6. Reference image to PNG image transformation 6.1 Color types and values 6.2 Alpha representation 7. Encoding the PNG image as a PNG datastream 7.1 Integers and byte order 7.2 Scanlines 7.3 Filtering 8. Interlacing and pass extraction Introduction 8.1 Interlace methods 9. Filtering 9.1 Filter methods and filter types 9.2 Filter types for filter method 0 9.3 Filter type 3: Average 9.4 Filter type 4: Paeth 10. Compression 10.1 Compression method 0 10.2 Compression of the sequence of filtered scanlines 10.3 Other uses of compression 11. Chunk specifications 11.1 General 11.2 Critical chunks Introduction 11.2.1 IHDR Image header 11.2.2 PLTE Palette 11.2.3 IDAT Image data 11.2.4 IEND Image trailer 11.3 Ancillary chunks Introduction 11.3.1 Transparency information 11.3.1.1 tRNS Transparency 11.3.2 Color space information 11.3.2.1 cHRM Primary chromaticities and white point 11.3.2.2 gAMA Image gamma 11.3.2.3 iCCP Embedded ICC profile 11.3.2.4 sBIT Significant bits 11.3.2.5 sRGB Standard RGB color space 11.3.2.6 cICP Coding-independent code points for video signal type identification 11.3.2.7 mDCV Mastering Display Color Volume 11.3.2.8 cLLI Content Light Level Information 11.3.3 Textual information Introduction 11.3.3.1 Keywords and text strings 11.3.3.2 tEXt Textual data 11.3.3.3 zTXt Compressed textual data 11.3.3.4 iTXt International textual data 11.3.4 Miscellaneous information 11.3.4.1 bKGD Background color 11.3.4.2 hIST Image histogram 11.3.4.3 pHYs Physical pixel dimensions 11.3.4.4 sPLT Suggested palette 11.3.4.5 eXIf Exchangeable Image File (Exif) Profile 11.3.4.5.1 eXIf General Recommendations 11.3.4.5.2 eXIf Recommendations for Decoders 11.3.4.5.3 eXIf Recommendations for Encoders 11.3.5 Time stamp information 11.3.5.1 tIME Image last-modification time 11.3.6 Animation information 11.3.6.1 acTL Animation Control Chunk 11.3.6.2 fcTL Frame Control Chunk 11.3.6.3 fdAT Frame Data Chunk 12. PNG Encoders Introduction 12.1 Encoder gamma handling 12.2 Encoder color handling 12.3 Alpha channel creation 12.4 Sample depth scaling 12.5 Suggested palettes 12.6 Interlacing 12.7 Filter selection 12.8 Compression 12.9 Text chunk processing 12.10 Chunking 12.10.1 Use of private chunks 12.10.2 Use of non-reserved field values 12.10.3 Ancillary chunks 13. PNG decoders and viewers Introduction 13.1 Error handling 13.2 Error checking 13.3 Security considerations 13.4 Privacy considerations 13.5 Chunking 13.6 Pixel dimensions 13.7 Text chunk processing 13.8 Decompression 13.9 Filtering 13.10 Interlacing and progressive display 13.11 Truecolor image handling 13.12 Sample depth rescaling 13.13 Decoder gamma handling 13.14 Decoder color handling 13.15 Background color 13.16 Alpha channel processing 13.17 Histogram and suggested palette usage 14. Editors 14.1 Additional chunk types 14.2 Behavior of PNG editors 14.3 Ordering of chunks 14.3.1 Ordering of critical chunks 14.3.2 Ordering of ancillary chunks 15. Conformance 15.1 Conformance 15.2 Introduction 15.2.1 Objectives 15.2.2 Scope 15.3 Conformance conditions 15.3.1 Conformance of PNG datastreams 15.3.2 Conformance of PNG encoders 15.3.3 Conformance of PNG decoders 15.3.4 Conformance of PNG editors A. Internet Media Types A.1 image/png A.2 image/apng B. Guidelines for private chunk types C. Gamma and chromaticity D. Sample CRC implementation E. Online resources Introduction E.1 ICC profile specifications E.2 PNG web site E.3 Sample implementation and test images F. Changes F.1 Changes since the Proposed Recommendation of 15 May 2025 F.2 Changes since the Candidate Recommendation Snapshot of 13 March 2025 F.3 Changes since the Candidate Recommendation Draft of 21 January 2025 (Third Edition) F.4 Changes since the Candidate Recommendation Draft of 18 July 2024 (Third Edition) F.5 Changes since the Candidate Recommendation Snapshot of 21 September 2023 (Third Edition) F.6 Changes since the Working Draft of 20 July 2023 (Third Edition) F.7 Changes since the First Public Working Draft of 25 October 2022 (Third Edition) F.8 Changes since the W3C Recommendation of 10 November 2003 (PNG Second Edition) F.9 Changes between First and Second Editions G. References G.1 Normative references G.2 Informative references 1. Introduction The design goals for this specification were: Portability: encoding, decoding, and transmission should be software and hardware platform independent. Completeness: it should be possible to represent truecolor , indexed-color , and greyscale images, in each case with
the option of transparency, color space information, and ancillary information such as textual comments. Serial encode and decode: it should be possible for datastreams to be generated serially and read serially, allowing the
datastream format to be used for on-the-fly generation and display of images across a serial communication channel. Progressive presentation: it should be possible to transmit datastreams so that an approximation of the whole image can be
is a frame.
Thus, for animated PNG, when the static image is not the first frame,
the static image is not considered to be a frame. frame buffer the final digital storage area for the image shown by most types of computer display. Note Software causes an image to appear on screen by loading the image into the frame buffer . fully transparent black pixel where the red, green, blue and alpha components are all equal to zero. gamma value value of the exponent of a gamma transfer function . gamma power-law transfer function . high dynamic range ( HDR ) an image format capable of storing images with a relatively high dynamic range similar to or in excess of the human visual system's instantaneous dynamic range (~12-14 stops ). PNG allows the use of two HDR formats, HLG and PQ [ ITU-R-BT.2100 ]. hybrid log-gamma ( HLG ) transfer function defined in [ ITU-R-BT.2100 ] Table 5. (A relative scene-referred system.) full-range image image where reference black and white correspond, respectively, to sample values 0 and 2 bit depth -
1 . image data 1-dimensional array of scanlines within an image. interlaced PNG image sequence of reduced images generated from the PNG image by pass extraction . lossless method of data compression that permits reconstruction of the original data exactly, bit-for-bit. luminance an objective measurement of the visible light intensity, taking into account the sensitivity of the human eye to different wavelengths. Note Luminance and chromaticity together fully define a measured color. For a formal definition, see [ COLORIMETRY ]. LZ77 data compression algorithm described in [ Ziv-Lempel ]. narrow-range image Image where reference black and white do not correspond, respectively, to sample values 0 and 2 bit depth - 1 . network byte order byte order in which the most significant byte comes first, then the less significant bytes in descending order of
significance ( MSB LSB for two-byte integers, MSB B2 B1 LSB for four-byte integers). perceptual quantizer ( PQ ) transfer function defined in [ ITU-R-BT.2100 ] Table 4. (An absolute display-referred system.) Note Only RGB may be used in PNG, ICtCp is NOT supported. PNG decoder process or device that reconstructs the reference image from a PNG datastream and generates a
corresponding delivered image . PNG editor process or device that creates a modification of an existing PNG datastream , preserving unmodified ancillary
information wherever possible, and obeying the chunk ordering rules, even for unknown chunk types. PNG encoder process or device which constructs a reference image from a source image , and generates a PNG
values. PNG two-byte unsigned integer a two-byte unsigned integer in network byte order. sample intersection of a channel and a pixel in an image. sample depth number of bits used to represent a sample value. scanline row of pixels within an image or interlaced PNG image . standard dynamic range ( SDR ) an image format capable of storing images with a relatively low dynamic range of 5-8 stops . Examples include [ SRGB ], [ Display-P3 ], [ ITU-R-BT.709 ]. Note Standard dynamic range is independent of the primaries and hence, gamut. Wide color gamut SDR formats are supported by PNG. stop a change in scene light luminance of a factor of 2. transfer function function relating image luminance with image samples. white point chromaticity of a computer display's nominal white value. zlib deflate -style compression method. SOURCE: [ rfc1950 ] Note Also refers to the name of a library containing a sample implementation of this method. Cyclic Redundancy Code CRC type of check value designed to detect most transmission errors. Note A decoder calculates the CRC for the received data and checks by comparing it to the CRC calculated by
the encoder and appended to the data. A mismatch indicates that the data or the CRC were corrupted in transit. Cathode Ray Tube CRT vacuum tube containing one or more electron guns, which emit electron beams that are manipulated to display images on a
phosphorescent screen. Electro-Optical Transfer Function EOTF The transfer function between the electrical or digital domain and light energy. It defines the amount of light emitted by a display for a given input signal. Least Significant Byte LSB Least significant byte of a multi- byte value. Most Significant Byte MSB Most significant byte of a multi- byte value. Opto-Electrical Transfer Function OETF The transfer function between light energy and the electrical or digital domain. It defines the amount of light in a scene required to produce a given output signal. 4. Concepts 4.1 Static and Animated images All PNG images contain a single static image . Some PNG images — called Animated PNG ( APNG ) — also
contain a frame-based animation sequence, the animated image . The first frame of this may be — but need not be —
the static image . Non-animation-capable displays (such as printers) will display the static image rather than
were widely adopted, enables the exact chromaticities of the RGB data to be specified, along with the gamma correction
to be applied (see C. Gamma and chromaticity ). However, color-aware applications will prefer one of the first three
methods, while color-unaware applications will typically ignore all four methods. Table 1 is a list of chunk types that provide color space information,
each with an associated Priority number. If a single image contains more than one of these chunk types,
the chunk with the lowest Priority number should take precedence and any higher-numbered chunk types should be ignored. Table 1 Color Chunk Priority Chunk Type Priority cICP 1 iCCP 2 sRGB 3 cHRM and gAMA 4 Gamma correction is not applied to the alpha channel, if present. Alpha samples are always full-range and represent
```

OCR OFF preview:

```text
the group; that page also includes
instructions for disclosing a patent. An individual who has actual
knowledge of a patent which the individual believes contains Essential Claim(s) must disclose the information in accordance with section 6 of the W3C Patent Policy . This document is governed by the 03 November 2023 W3C Process Document . Table of Contents Abstract Status of This Document 1. Introduction 2. Scope 3. Terms, definitions, and abbreviated terms 4. Concepts 4.1 Static and Animated images 4.2 Images 4.3 Color spaces 4.4 Reference image to PNG image transformation Introduction 4.4.1 Alpha separation 4.4.2 Indexing 4.4.3 RGB merging 4.4.4 Alpha compaction 4.4.5 Sample depth scaling 4.5 PNG image 4.6 Encoding the PNG image Introduction 4.6.1 Pass extraction 4.6.2 Scanline serialization 4.6.3 Filtering 4.6.4 Compression 4.6.5 Chunking 4.7 Additional information 4.8 PNG datastream 4.8.1 Chunks 4.8.2 Chunk types 4.9 APNG : frame-based animation Introduction 4.9.1 Structure 4.9.2 Sequence numbers 4.9.3 Output buffer 4.9.4 Canvas 4.10 Error handling 4.11 Extensions 5. Datastream structure 5.1 PNG datastream 5.2 PNG signature 5.3 Chunk layout 5.4 Chunk naming conventions 5.5 CRC algorithm 5.6 Chunk ordering 5.7 Defining chunks 5.7.1 General 5.7.2 Defining public chunks 5.7.3 Defining private chunks 5.8 Private field values 6. Reference image to PNG image transformation 6.1 Color types and values 6.2 Alpha representation 7. Encoding the PNG image as a PNG datastream 7.1 Integers and byte order 7.2 Scanlines 7.3 Filtering 8. Interlacing and pass extraction Introduction 8.1 Interlace methods 9. Filtering 9.1 Filter methods and filter types 9.2 Filter types for filter method 0 9.3 Filter type 3: Average 9.4 Filter type 4: Paeth 10. Compression 10.1 Compression method 0 10.2 Compression of the sequence of filtered scanlines 10.3 Other uses of compression 11. Chunk specifications 11.1 General 11.2 Critical chunks Introduction 11.2.1 IHDR Image header 11.2.2 PLTE Palette 11.2.3 IDAT Image data 11.2.4 IEND Image trailer 11.3 Ancillary chunks Introduction 11.3.1 Transparency information 11.3.1.1 tRNS Transparency 11.3.2 Color space information 11.3.2.1 cHRM Primary chromaticities and white point 11.3.2.2 gAMA Image gamma 11.3.2.3 iCCP Embedded ICC profile 11.3.2.4 sBIT Significant bits 11.3.2.5 sRGB Standard RGB color space 11.3.2.6 cICP Coding-independent code points for video signal type identification 11.3.2.7 mDCV Mastering Display Color Volume 11.3.2.8 cLLI Content Light Level Information 11.3.3 Textual information Introduction 11.3.3.1 Keywords and text strings 11.3.3.2 tEXt Textual data 11.3.3.3 zTXt Compressed textual data 11.3.3.4 iTXt International textual data 11.3.4 Miscellaneous information 11.3.4.1 bKGD Background color 11.3.4.2 hIST Image histogram 11.3.4.3 pHYs Physical pixel dimensions 11.3.4.4 sPLT Suggested palette 11.3.4.5 eXIf Exchangeable Image File (Exif) Profile 11.3.4.5.1 eXIf General Recommendations 11.3.4.5.2 eXIf Recommendations for Decoders 11.3.4.5.3 eXIf Recommendations for Encoders 11.3.5 Time stamp information 11.3.5.1 tIME Image last-modification time 11.3.6 Animation information 11.3.6.1 acTL Animation Control Chunk 11.3.6.2 fcTL Frame Control Chunk 11.3.6.3 fdAT Frame Data Chunk 12. PNG Encoders Introduction 12.1 Encoder gamma handling 12.2 Encoder color handling 12.3 Alpha channel creation 12.4 Sample depth scaling 12.5 Suggested palettes 12.6 Interlacing 12.7 Filter selection 12.8 Compression 12.9 Text chunk processing 12.10 Chunking 12.10.1 Use of private chunks 12.10.2 Use of non-reserved field values 12.10.3 Ancillary chunks 13. PNG decoders and viewers Introduction 13.1 Error handling 13.2 Error checking 13.3 Security considerations 13.4 Privacy considerations 13.5 Chunking 13.6 Pixel dimensions 13.7 Text chunk processing 13.8 Decompression 13.9 Filtering 13.10 Interlacing and progressive display 13.11 Truecolor image handling 13.12 Sample depth rescaling 13.13 Decoder gamma handling 13.14 Decoder color handling 13.15 Background color 13.16 Alpha channel processing 13.17 Histogram and suggested palette usage 14. Editors 14.1 Additional chunk types 14.2 Behavior of PNG editors 14.3 Ordering of chunks 14.3.1 Ordering of critical chunks 14.3.2 Ordering of ancillary chunks 15. Conformance 15.1 Conformance 15.2 Introduction 15.2.1 Objectives 15.2.2 Scope 15.3 Conformance conditions 15.3.1 Conformance of PNG datastreams 15.3.2 Conformance of PNG encoders 15.3.3 Conformance of PNG decoders 15.3.4 Conformance of PNG editors A. Internet Media Types A.1 image/png A.2 image/apng B. Guidelines for private chunk types C. Gamma and chromaticity D. Sample CRC implementation E. Online resources Introduction E.1 ICC profile specifications E.2 PNG web site E.3 Sample implementation and test images F. Changes F.1 Changes since the Proposed Recommendation of 15 May 2025 F.2 Changes since the Candidate Recommendation Snapshot of 13 March 2025 F.3 Changes since the Candidate Recommendation Draft of 21 January 2025 (Third Edition) F.4 Changes since the Candidate Recommendation Draft of 18 July 2024 (Third Edition) F.5 Changes since the Candidate Recommendation Snapshot of 21 September 2023 (Third Edition) F.6 Changes since the Working Draft of 20 July 2023 (Third Edition) F.7 Changes since the First Public Working Draft of 25 October 2022 (Third Edition) F.8 Changes since the W3C Recommendation of 10 November 2003 (PNG Second Edition) F.9 Changes between First and Second Editions G. References G.1 Normative references G.2 Informative references 1. Introduction The design goals for this specification were: Portability: encoding, decoding, and transmission should be software and hardware platform independent. Completeness: it should be possible to represent truecolor , indexed-color , and greyscale images, in each case with
the option of transparency, color space information, and ancillary information such as textual comments. Serial encode and decode: it should be possible for datastreams to be generated serially and read serially, allowing the
datastream format to be used for on-the-fly generation and display of images across a serial communication channel. Progressive presentation: it should be possible to transmit datastreams so that an approximation of the whole image can be
is a frame.
Thus, for animated PNG, when the static image is not the first frame,
the static image is not considered to be a frame. frame buffer the final digital storage area for the image shown by most types of computer display. Note Software causes an image to appear on screen by loading the image into the frame buffer . fully transparent black pixel where the red, green, blue and alpha components are all equal to zero. gamma value value of the exponent of a gamma transfer function . gamma power-law transfer function . high dynamic range ( HDR ) an image format capable of storing images with a relatively high dynamic range similar to or in excess of the human visual system's instantaneous dynamic range (~12-14 stops ). PNG allows the use of two HDR formats, HLG and PQ [ ITU-R-BT.2100 ]. hybrid log-gamma ( HLG ) transfer function defined in [ ITU-R-BT.2100 ] Table 5. (A relative scene-referred system.) full-range image image where reference black and white correspond, respectively, to sample values 0 and 2 bit depth -
1 . image data 1-dimensional array of scanlines within an image. interlaced PNG image sequence of reduced images generated from the PNG image by pass extraction . lossless method of data compression that permits reconstruction of the original data exactly, bit-for-bit. luminance an objective measurement of the visible light intensity, taking into account the sensitivity of the human eye to different wavelengths. Note Luminance and chromaticity together fully define a measured color. For a formal definition, see [ COLORIMETRY ]. LZ77 data compression algorithm described in [ Ziv-Lempel ]. narrow-range image Image where reference black and white do not correspond, respectively, to sample values 0 and 2 bit depth - 1 . network byte order byte order in which the most significant byte comes first, then the less significant bytes in descending order of
significance ( MSB LSB for two-byte integers, MSB B2 B1 LSB for four-byte integers). perceptual quantizer ( PQ ) transfer function defined in [ ITU-R-BT.2100 ] Table 4. (An absolute display-referred system.) Note Only RGB may be used in PNG, ICtCp is NOT supported. PNG decoder process or device that reconstructs the reference image from a PNG datastream and generates a
corresponding delivered image . PNG editor process or device that creates a modification of an existing PNG datastream , preserving unmodified ancillary
information wherever possible, and obeying the chunk ordering rules, even for unknown chunk types. PNG encoder process or device which constructs a reference image from a source image , and generates a PNG
values. PNG two-byte unsigned integer a two-byte unsigned integer in network byte order. sample intersection of a channel and a pixel in an image. sample depth number of bits used to represent a sample value. scanline row of pixels within an image or interlaced PNG image . standard dynamic range ( SDR ) an image format capable of storing images with a relatively low dynamic range of 5-8 stops . Examples include [ SRGB ], [ Display-P3 ], [ ITU-R-BT.709 ]. Note Standard dynamic range is independent of the primaries and hence, gamut. Wide color gamut SDR formats are supported by PNG. stop a change in scene light luminance of a factor of 2. transfer function function relating image luminance with image samples. white point chromaticity of a computer display's nominal white value. zlib deflate -style compression method. SOURCE: [ rfc1950 ] Note Also refers to the name of a library containing a sample implementation of this method. Cyclic Redundancy Code CRC type of check value designed to detect most transmission errors. Note A decoder calculates the CRC for the received data and checks by comparing it to the CRC calculated by
the encoder and appended to the data. A mismatch indicates that the data or the CRC were corrupted in transit. Cathode Ray Tube CRT vacuum tube containing one or more electron guns, which emit electron beams that are manipulated to display images on a
phosphorescent screen. Electro-Optical Transfer Function EOTF The transfer function between the electrical or digital domain and light energy. It defines the amount of light emitted by a display for a given input signal. Least Significant Byte LSB Least significant byte of a multi- byte value. Most Significant Byte MSB Most significant byte of a multi- byte value. Opto-Electrical Transfer Function OETF The transfer function between light energy and the electrical or digital domain. It defines the amount of light in a scene required to produce a given output signal. 4. Concepts 4.1 Static and Animated images All PNG images contain a single static image . Some PNG images — called Animated PNG ( APNG ) — also
contain a frame-based animation sequence, the animated image . The first frame of this may be — but need not be —
the static image . Non-animation-capable displays (such as printers) will display the static image rather than
were widely adopted, enables the exact chromaticities of the RGB data to be specified, along with the gamma correction
to be applied (see C. Gamma and chromaticity ). However, color-aware applications will prefer one of the first three
methods, while color-unaware applications will typically ignore all four methods. Table 1 is a list of chunk types that provide color space information,
each with an associated Priority number. If a single image contains more than one of these chunk types,
the chunk with the lowest Priority number should take precedence and any higher-numbered chunk types should be ignored. Table 1 Color Chunk Priority Chunk Type Priority cICP 1 iCCP 2 sRGB 3 cHRM and gAMA 4 Gamma correction is not applied to the alpha channel, if present. Alpha samples are always full-range and represent
```

### benchmark_samples/repo_sample.doc

- Extension: doc
- Size bytes: 22016
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: n/a
- Table check reason: No strong table expectation for this file type.

OCR ON preview:

```text
Test OLE file, saved as Word 97-2003 Document.
[Content_Types].xml
_rels/.rels
theme/theme/themeManager.xml
theme/theme/theme1.xml
w toc'v
3Vq%'#q
:\TZaG
Qg20pp
theme/theme/_rels/themeManager.xml.rels
K(M&$R(.1
[Content_Types].xmlPK
_rels/.relsPK
theme/theme/themeManager.xmlPK
theme/theme/theme1.xmlPK
theme/theme/_rels/themeManager.xml.relsPK
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:clrMap xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
Laurence Ipsum
Normal.dotm
Microsoft Office Word
Microsoft Word 97-2003 Document
```

OCR OFF preview:

```text
Test OLE file, saved as Word 97-2003 Document.
[Content_Types].xml
_rels/.rels
theme/theme/themeManager.xml
theme/theme/theme1.xml
w toc'v
3Vq%'#q
:\TZaG
Qg20pp
theme/theme/_rels/themeManager.xml.rels
K(M&$R(.1
[Content_Types].xmlPK
_rels/.relsPK
theme/theme/themeManager.xmlPK
theme/theme/theme1.xmlPK
theme/theme/_rels/themeManager.xml.relsPK
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:clrMap xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
Laurence Ipsum
Normal.dotm
Microsoft Office Word
Microsoft Word 97-2003 Document
```

### benchmark_samples/repo_sample.pptx

- Extension: pptx
- Size bytes: 366536
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: n/a
- Table check reason: No strong table expectation for this file type.

OCR ON preview:

```text
## Slide 1 | Layout: Blank
Chart: Series 1: -4.3, 2.5, 3.5, -4.5 ; Series 2: 2.4, -4.4, 1.8, 2.8 ; Series 3: 2.0, 2.0, -3.0, 5.0
## Slide 2 | Layout: Blank
Chart: Series 1: 94.3, 2.5, 3.5, 4.5 ; Series 2: 2.4, 4.4, 1.8, 2.8 ; Series 3: 2.0, 2.0, 3.0, 5.0
## Slide 3 | Layout: Blank
Chart: value_axis.crosses == XL_AXIS_CROSSES.MAXIMUM | Y-Value 1: 2.7, 3.2, 0.8
## Slide 4 | Layout: Blank
Chart: value_axis.crosses == XL_AXIS_CROSSES.MINIMUM | Y-Value 1: 2.7, 3.2, -3.8
## Slide 5 | Layout: Blank
Chart: Y-Value 1: 2.7, 3.2, 0.8
## Slide 6 | Layout: Blank
Chart: Y-Value 1: 2.7, -3.2, 0.8
## Slide 7 | Layout: Blank
Chart: Series 1: 4.3, 2.5, 3.5, 4.5, 3.6, 15.0, 17.0
## Slide 8 | Layout: Blank
Chart: Series 1: 4.3, 2.5, 3.5, 4.5 ; Series 2: 2.4, 4.4, 1.8, 2.8 ; Series 3: 2.0, 2.0, 3.0, 5.0
```

OCR OFF preview:

```text
## Slide 1 | Layout: Blank
Chart: Series 1: -4.3, 2.5, 3.5, -4.5 ; Series 2: 2.4, -4.4, 1.8, 2.8 ; Series 3: 2.0, 2.0, -3.0, 5.0
## Slide 2 | Layout: Blank
Chart: Series 1: 94.3, 2.5, 3.5, 4.5 ; Series 2: 2.4, 4.4, 1.8, 2.8 ; Series 3: 2.0, 2.0, 3.0, 5.0
## Slide 3 | Layout: Blank
Chart: value_axis.crosses == XL_AXIS_CROSSES.MAXIMUM | Y-Value 1: 2.7, 3.2, 0.8
## Slide 4 | Layout: Blank
Chart: value_axis.crosses == XL_AXIS_CROSSES.MINIMUM | Y-Value 1: 2.7, 3.2, -3.8
## Slide 5 | Layout: Blank
Chart: Y-Value 1: 2.7, 3.2, 0.8
## Slide 6 | Layout: Blank
Chart: Y-Value 1: 2.7, -3.2, 0.8
## Slide 7 | Layout: Blank
Chart: Series 1: 4.3, 2.5, 3.5, 4.5, 3.6, 15.0, 17.0
## Slide 8 | Layout: Blank
Chart: Series 1: 4.3, 2.5, 3.5, 4.5 ; Series 2: 2.4, 4.4, 1.8, 2.8 ; Series 3: 2.0, 2.0, 3.0, 5.0
```

### benchmark_samples/sample_data.csv

- Extension: csv
- Size bytes: 3858
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: pass
- Table check reason: Expected [TABLE_START] marker found for tabular input.

OCR ON preview:

```text
[TABLE_START]
| sepal_length | sepal_width | petal_length | petal_width | species |
| --- | --- | --- | --- | --- |
```

OCR OFF preview:

```text
[TABLE_START]
| sepal_length | sepal_width | petal_length | petal_width | species |
| --- | --- | --- | --- | --- |
```

### benchmark_samples/sample_data.json

- Extension: json
- Size bytes: 100492
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: n/a
- Table check reason: No strong table expectation for this file type.

OCR ON preview:

```text
[122].Year: 1973-01-01
[122].Origin: USA
[123].Name: pontiac grand prix
[123].Miles_per_Gallon: 16
[123].Cylinders: 8
[235].Year: 1977-01-01
[235].Origin: USA
[236].Name: pontiac grand prix lj
[236].Miles_per_Gallon: 16
[236].Cylinders: 8
```

OCR OFF preview:

```text
[122].Year: 1973-01-01
[122].Origin: USA
[123].Name: pontiac grand prix
[123].Miles_per_Gallon: 16
[123].Cylinders: 8
[235].Year: 1977-01-01
[235].Origin: USA
[236].Name: pontiac grand prix lj
[236].Miles_per_Gallon: 16
[236].Cylinders: 8
```

### benchmark_samples/sample_xml.xml

- Extension: xml
- Size bytes: 164
- Quality severity: ok
- Chars gain (ON - OFF): 0
- Table gain (ON - OFF): 0
- OCR ON error kind: none
- OCR OFF error kind: none
- Table check status: n/a
- Table check reason: No strong table expectation for this file type.

OCR ON preview:

```text
/note/to<to>: Tove
/note/from<from>: Jani
/note/heading<heading>: Reminder
/note/body<body>: Don't forget me this weekend!
```

OCR OFF preview:

```text
/note/to<to>: Tove
/note/from<from>: Jani
/note/heading<heading>: Reminder
/note/body<body>: Don't forget me this weekend!
```
