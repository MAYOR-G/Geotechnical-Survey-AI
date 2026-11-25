// ============================================================================
// MASTER TYPST TEMPLATE: OFFSHORE MARINE GEOTECHNICAL SURVEY FIELD REPORT
// ============================================================================

#let render-offshore-report(
  client-name: "Client / Operator",
  contractor-name: "Lead Survey Contractor",
  partner-name: "Geotechnical Partner",
  program-title: "OFFSHORE FIELD DEVELOPMENT CAMPAIGN",
  report-title: "GEOTECHNICAL SURVEY FIELD REPORT",
  report-subtitle: "Offshore Geotechnical Investigation",
  client-ref: "CLIENT-REF-001",
  contractor-ref: "CONT-REF-001",
  revision-number: "Rev 01",
  fao-text: "Offshore Engineering Directorate",
  client-logo: none,
  contractor-logo: none,
  partner-logo: none,
  signature-img: none,
  revision-rows: (),
  auth-prepared: (:),
  auth-reviewed: (:),
  auth-approved1: (:),
  auth-approved2: (:),
  body-content: [],
) = {
  set document(title: report-title, author: contractor-name)
  set text(font: ("Helvetica Neue", "Arial", "Liberation Sans"), size: 10pt, fill: rgb("#1D1D1F"))
  set par(justify: true, leading: 0.68em, spacing: 1.02em)
  set heading(numbering: none)
  show figure.where(kind: table): set block(breakable: true)
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: image): set block(breakable: false)

  show heading.where(level: 1): it => block(
    above: 1.75em,
    below: 0.85em,
    breakable: false,
    sticky: true,
    stroke: (bottom: 0.8pt + rgb("#1D1D1F")),
    inset: (bottom: 5pt),
    text(size: 12.8pt, weight: "bold", fill: rgb("#1D1D1F"), upper(it.body))
  )

  show heading.where(level: 2): it => block(
    above: 1.3em,
    below: 0.6em,
    breakable: false,
    sticky: true,
    text(size: 11pt, weight: "bold", fill: rgb("#1D1D1F"), it.body)
  )

  show heading.where(level: 3): it => block(
    above: 1.0em,
    below: 0.5em,
    breakable: false,
    sticky: true,
    text(size: 10.2pt, weight: "bold", fill: rgb("#333333"), it.body)
  )

  let running-header() = {
    table(
      columns: (48%, 52%),
      stroke: 0.6pt + rgb("#1D1D1F"),
      inset: (x: 8pt, y: 5pt),
      align: (left + horizon, right + horizon),
      if client-logo != none {
        image(client-logo, height: 24pt, fit: "contain")
      } else {
        text(weight: "bold", size: 9pt, client-name)
      },
      grid(
        columns: (auto, auto),
        gutter: 10pt,
        align: right + horizon,
        if contractor-logo != none {
          image(contractor-logo, height: 22pt, fit: "contain")
        } else {
          text(weight: "bold", size: 8.5pt, contractor-name)
        },
        if partner-logo != none {
          image(partner-logo, height: 18pt, fit: "contain")
        } else {
          []
        }
      )
    )
  }

  let running-footer() = {
    line(length: 100%, stroke: 0.5pt + rgb("#E0E0E0"))
    v(3pt)
    grid(
      columns: (1fr, auto),
      text(size: 8pt, fill: rgb("#4B5565"), contractor-ref + "  |  " + report-title),
      text(size: 8pt, weight: "bold", fill: rgb("#1D1D1F"), [
        Page #context counter(page).display("1 of 1", both: true)
      ])
    )
  }

  // ==========================================================================
  // PAGE 1: DEDICATED CORPORATE BORDERED COVER PAGE
  // ==========================================================================
  page(
    paper: "a4",
    margin: (top: 1.6cm, bottom: 1.6cm, left: 1.8cm, right: 1.8cm),
    header: none,
    footer: none,
  )[
    #rect(width: 100%, height: 100%, stroke: 0.9pt + rgb("#1D1D1F"), inset: 0pt)[
      #grid(
        rows: (auto, 1fr, auto, auto, auto, auto),
        running-header(),
        align(center + horizon)[
          #pad(x: 24pt)[
            #text(size: 13.5pt, weight: "bold", fill: rgb("#0066CC"), program-title)
            #v(18pt)
            #text(size: 19.5pt, weight: "bold", fill: rgb("#1D1D1F"), upper(report-title))
            #v(12pt)
            #text(size: 14pt, weight: "bold", fill: rgb("#333333"), report-subtitle)
          ]
        ],
        block(
          width: 100%,
          stroke: (top: 0.7pt + rgb("#1D1D1F"), bottom: 0.7pt + rgb("#1D1D1F")),
          inset: (y: 10pt),
          align(center)[#text(size: 11.5pt, weight: "bold", [Revision: #revision-number])]
        ),
        block(
          width: 100%,
          stroke: (bottom: 0.7pt + rgb("#1D1D1F")),
          inset: (y: 10pt, x: 14pt),
          align(center)[
            #text(size: 10pt, weight: "bold", [#client-name Document Ref.: #client-ref]) \
            #v(3pt)
            #text(size: 10pt, weight: "bold", [#contractor-name Document Ref.: #contractor-ref])
          ]
        ),
        block(
          width: 100%,
          stroke: (bottom: 0.7pt + rgb("#1D1D1F")),
          inset: 10pt,
          text(size: 8.2pt, fill: rgb("#333333"), [
            This document is proprietary and confidential. Copyright is vested in #contractor-name. All rights reserved. Neither the whole nor any part of this document may be disclosed to any third party nor reproduced, stored in any retrieval system, or transmitted in any form or by any means without the prior written consent of the copyright owner.
          ])
        ),
        table(
          columns: (10%, 15%, 36%, 13%, 13%, 13%),
          stroke: 0.6pt + rgb("#1D1D1F"),
          inset: 5pt,
          align: center + horizon,
          ..revision-rows.flatten(),
          table.cell(fill: rgb("#F5F5F7"))[*Rev*],
          table.cell(fill: rgb("#F5F5F7"))[*Date*],
          table.cell(fill: rgb("#F5F5F7"))[*Reason for Revision*],
          table.cell(fill: rgb("#F5F5F7"))[*Prepared*],
          table.cell(fill: rgb("#F5F5F7"))[*Checked*],
          table.cell(fill: rgb("#F5F5F7"))[*Approved*],
        )
      )
    ]
  ]

  // ==========================================================================
  // PAGE 2+: RUNNING CORPORATE HEADER & FOOTER
  // ==========================================================================
  set page(
    paper: "a4",
    margin: (top: 2.8cm, bottom: 2.2cm, left: 2.0cm, right: 2.0cm),
    header: running-header(),
    footer: running-footer(),
  )

  heading(level: 1, outlined: false)[DOCUMENT AUTHORISATION AND DISTRIBUTION]
  table(
    columns: (26%, 48%, 26%),
    stroke: 0.6pt + rgb("#1D1D1F"),
    inset: 6pt,
    table.header(
      table.cell(colspan: 3, fill: rgb("#F5F5F7"))[*Document Authorisation and Distribution*],
    ),
    [*Contractor*], table.cell(colspan: 2)[#contractor-name],
    [*Client*], table.cell(colspan: 2)[#client-name],
    [*FAO*], table.cell(colspan: 2)[#fao-text],
    [*Document Ref.*], table.cell(colspan: 2)[#contractor-ref],
    [*Title*], table.cell(colspan: 2)[#report-title — #report-subtitle],
    [*Prepared By*], [#auth-prepared.at("name", default: "Lead Geotechnical Engineer")], [Date: #auth-prepared.at("date", default: "2026")],
    [*Reviewed By*], [#auth-reviewed.at("name", default: "Principal Reviewer")], [Date: #auth-reviewed.at("date", default: "2026")],
    [*Approved By*], [#auth-approved1.at("name", default: "Technical Director")], [Date: #auth-approved1.at("date", default: "2026")],
    [*Authorised Copies*], [Original: #client-name], [Copy No. 1: #contractor-name],
  )

  v(8pt)
  text(size: 9.5pt)[This document has been approved and authorised by the authorities whose signatures appear below:]
  v(4pt)
  table(
    columns: (16%, 21%, 21%, 21%, 21%),
    stroke: 0.6pt + rgb("#1D1D1F"),
    inset: 6pt,
    table.header(
      table.cell(fill: rgb("#F5F5F7"))[],
      table.cell(fill: rgb("#F5F5F7"))[*Prepared By*],
      table.cell(fill: rgb("#F5F5F7"))[*Reviewed By*],
      table.cell(fill: rgb("#F5F5F7"))[*Approved By*],
      table.cell(fill: rgb("#F5F5F7"))[*Approved By*],
    ),
    [*Signature*],
    if signature-img != none { image(signature-img, height: 22pt, fit: "contain") } else { [—] },
    [—],
    [—],
    [—],
    [*Name*],
    [#auth-prepared.at("name", default: "Lead Geotechnical Engineer")],
    [#auth-reviewed.at("name", default: "Principal Reviewer")],
    [#auth-approved1.at("name", default: "Technical Director")],
    [#auth-approved2.at("name", default: "Client Representative")],
    [*Designation*],
    [#auth-prepared.at("designation", default: "Lead Geotechnical Engineer")],
    [#auth-reviewed.at("designation", default: "Principal Geoscientist")],
    [#auth-approved1.at("designation", default: "Technical Director")],
    [#auth-approved2.at("designation", default: "Project Lead")],
    [*Date*],
    [#auth-prepared.at("date", default: "2026")],
    [#auth-reviewed.at("date", default: "2026")],
    [#auth-approved1.at("date", default: "2026")],
    [#auth-approved2.at("date", default: "2026")],
  )

  v(14pt)
  outline(title: [TABLE OF CONTENTS], indent: auto, depth: 2)
  v(12pt)
  outline(title: [LIST OF TABLES], target: figure.where(kind: table))
  v(12pt)
  outline(title: [LIST OF FIGURES], target: figure.where(kind: image))

  pagebreak()

  // MAIN REPORT BODY
  body-content
}
