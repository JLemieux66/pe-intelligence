"""
Metadata service for business logic and data processing
"""
from typing import List, Dict, Any
from sqlalchemy import func, distinct
from backend.services.base import BaseService
from backend.schemas.responses import LocationsResponse, PitchBookMetadataResponse, IndustriesResponse
from src.models.database_models_v2 import Company, CompanyTag


class MetadataService(BaseService):
    """Service for metadata-related business logic"""
    
    def get_locations(self) -> LocationsResponse:
        """Get all unique locations from companies"""
        
        # Get unique countries
        countries = self.session.query(distinct(Company.country)).filter(
            Company.country.isnot(None)
        ).order_by(Company.country).all()
        countries_list = [c[0] for c in countries if c[0]]
        
        # Get unique states/regions
        states = self.session.query(distinct(Company.state_region)).filter(
            Company.state_region.isnot(None)
        ).order_by(Company.state_region).all()
        states_list = [s[0] for s in states if s[0]]
        
        # Get unique cities
        cities = self.session.query(distinct(Company.city)).filter(
            Company.city.isnot(None)
        ).order_by(Company.city).all()
        cities_list = [c[0] for c in cities if c[0]]
        
        return LocationsResponse(
            countries=countries_list,
            states=states_list,
            cities=cities_list
        )
    
    def get_pitchbook_metadata(self) -> PitchBookMetadataResponse:
        """Get PitchBook-specific metadata"""
        
        # Get unique industry groups
        industry_groups = self.session.query(distinct(Company.primary_industry_group)).filter(
            Company.primary_industry_group.isnot(None)
        ).order_by(Company.primary_industry_group).all()
        industry_groups_list = [ig[0] for ig in industry_groups if ig[0]]
        
        # Get unique industry sectors
        industry_sectors = self.session.query(distinct(Company.primary_industry_sector)).filter(
            Company.primary_industry_sector.isnot(None)
        ).order_by(Company.primary_industry_sector).all()
        industry_sectors_list = [is_[0] for is_ in industry_sectors if is_[0]]
        
        # Get unique verticals (these are comma-separated, so we need to split them)
        verticals_raw = self.session.query(distinct(Company.verticals)).filter(
            Company.verticals.isnot(None)
        ).all()
        
        # Parse comma-separated verticals
        verticals_set = set()
        for v_row in verticals_raw:
            if v_row[0]:
                # Split by comma and clean up
                for vertical in v_row[0].split(','):
                    cleaned = vertical.strip()
                    if cleaned:
                        verticals_set.add(cleaned)
        
        verticals_list = sorted(list(verticals_set))
        
        # Get unique HQ locations
        hq_locations = self.session.query(distinct(Company.hq_location)).filter(
            Company.hq_location.isnot(None)
        ).order_by(Company.hq_location).all()
        hq_locations_list = [hq[0] for hq in hq_locations if hq[0]]
        
        # Get unique HQ countries
        hq_countries = self.session.query(distinct(Company.hq_country)).filter(
            Company.hq_country.isnot(None)
        ).order_by(Company.hq_country).all()
        hq_countries_list = [hq[0] for hq in hq_countries if hq[0]]
        
        return PitchBookMetadataResponse(
            industry_groups=industry_groups_list,
            industry_sectors=industry_sectors_list,
            verticals=verticals_list,
            hq_locations=hq_locations_list,
            hq_countries=hq_countries_list
        )
    
    def get_industries(self) -> IndustriesResponse:
        """Get all unique industry tags"""
        
        # Get unique industry tags (excluding 'Other')
        industries = self.session.query(distinct(CompanyTag.tag_value)).filter(
            CompanyTag.tag_category == 'industry',
            CompanyTag.tag_value != 'Other'
        ).order_by(CompanyTag.tag_value).all()
        industries_list = [i[0] for i in industries if i[0]]
        
        # Get unique industry categories
        categories = self.session.query(distinct(Company.industry_category)).filter(
            Company.industry_category.isnot(None)
        ).order_by(Company.industry_category).all()
        categories_list = [c[0] for c in categories if c[0]]
        
        return IndustriesResponse(
            industries=industries_list,
            categories=categories_list
        )