#include <iostream>

#include "OSUT3Analysis/AnaTools/interface/ExternTemplates.h"
#include "OSUT3Analysis/AnaTools/interface/ValueLookup.h"

//!jet valueLookup
double
ValueLookup::valueLookup (const BNjet &object, string variable){

/*  BNjet jetCorr;
  if (flagJESJERCorr_) {
    jetCorr = getCorrectedJet(*object, jESJERCorr_);
    object = &jetCorr;
  }*/

  double value = 0.0;
  BNjet *obj = new BNjet (object);

  try
    {
      value = getMember ("BNjet", obj, variable);
    }
  catch (...)
    {
      //user defined variable
      if(variable == "disappTrkLeadingJetID") {
        value = object.pt > 110
          && fabs(object.eta) < 2.4
          && object.chargedHadronEnergyFraction > 0.2
          && object.neutralHadronEnergyFraction < 0.7
          && object.chargedEmEnergyFraction < 0.5
          && object.neutralEmEnergyFraction < 0.7;
      }

      else if(variable == "disappTrkSubLeadingJetID") {
        value = object.pt > 30
          && fabs(object.eta) < 4.5
          && object.neutralHadronEnergyFraction < 0.7
          && object.chargedEmEnergyFraction < 0.5;
          }

      else if(variable == "dPhiMet") {
        if (const BNmet *met = chosenMET ()) {
          value = deltaPhi (object.phi, met->phi);
        } else value = numeric_limits<int>::min ();
      }

      else if(variable == "metPt") {  // allow making 2D plots of jet quantities vs. Met
        if (const BNmet *met = chosenMET ()) {
          value = met->pt;
        } else value = numeric_limits<int>::min ();
      }

/*      else if(variable == "isLeadingPtJet") {
        double ptMax = -99;
        for (uint ijet = 0; ijet<jets->size(); ijet++) {
          double jetPt = valueLookup(&jets->at(ijet), "pt");
          if (jetPt > ptMax) ptMax = jetPt;
        }
        if (object.pt < ptMax) value = 0;
        else                    value = 1;
      }*/

/*      else if(variable == "deltaRMuonPt20") {
        // calculate the minimum deltaR between the jet and any muon with pT>20 GeV
        double deltaRMin = 99;
        if (!muons.product()) clog << "ERROR:  cannot find deltaRMuonPt20 because muons collection is not initialized." << endl;
        for (uint imuon = 0; imuon<muons->size(); imuon++) {
          double muonPt = valueLookup(&muons->at(imuon), "pt");
          if (muonPt < 20) continue;
          double muonEta = valueLookup(&muons->at(imuon), "eta");
          double muonPhi = valueLookup(&muons->at(imuon), "phi");
          double dR = deltaR(object.eta, object.phi, muonEta, muonPhi);
          if (dR < deltaRMin) deltaRMin = dR;
        }
        value = deltaRMin;
      }*/
      else{
        clog << "WARNING: invalid jet variable '" << variable << "'\n";
        value = numeric_limits<int>::min ();
      }
    }

  delete obj;
  return value;
} // end jet valueLookup
